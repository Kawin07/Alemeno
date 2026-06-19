import uuid
import logging
from datetime import datetime
from app.worker.celery_app import celery
from app.database import SyncSessionLocal
from app.models import Job, Transaction, JobSummary
from app.services.csv_parser import parse_csv
from app.services.data_cleaner import clean_data
from app.services.anomaly_detector import detect_anomalies
from app.services.llm_service import classify_transactions, generate_narrative
import math

logger = logging.getLogger(__name__)

@celery.task(name="app.worker.tasks.process_csv_job")
def process_csv_job(job_id_str: str):
    logger.info(f"Starting processing for job {job_id_str}")
    
    with SyncSessionLocal() as db:
        try:
            job_id = uuid.UUID(job_id_str)
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id_str} not found in database.")
                return
                
            job.status = "processing"
            db.commit()
            
            # 1. Parsing & Cleaning
            df = parse_csv(job.file_content)
            df_clean = clean_data(df)
            job.row_count_clean = len(df_clean)
            db.commit()
            
            # 2. Anomaly Detection
            df_anomaly = detect_anomalies(df_clean)
            
            # 3. LLM Classification for uncategorised
            records = df_anomaly.to_dict(orient='records')
            
            uncategorised = []
            for i, r in enumerate(records):
                if r.get('category') == 'Uncategorised':
                    uncategorised.append({
                        "txn_idx": i,
                        "merchant": r.get('merchant'),
                        "amount": r.get('amount'),
                        "notes": r.get('notes')
                    })
            
            llm_cat_failed = False
            raw_cat_response = None
            if uncategorised:
                updated_uncategorised, raw_cat_response, llm_cat_failed = classify_transactions(uncategorised)
                if not llm_cat_failed:
                    for item in updated_uncategorised:
                        idx = item.get('txn_idx')
                        cat = item.get('llm_category')
                        if cat:
                            records[idx]['llm_category'] = cat
                            records[idx]['category'] = cat # overwrite for summary purposes
            
            # 4. Aggregations for summary
            total_inr = sum(r['amount'] for r in records if r['currency'] == 'INR' and not math.isnan(r['amount']))
            total_usd = sum(r['amount'] for r in records if r['currency'] == 'USD' and not math.isnan(r['amount']))
            anomaly_count = sum(1 for r in records if r.get('is_anomaly'))
            
            merchant_spend = {}
            for r in records:
                m = r['merchant']
                merchant_spend[m] = merchant_spend.get(m, 0) + (r['amount'] if not math.isnan(r['amount']) else 0)
                
            top_merchants = sorted(merchant_spend.items(), key=lambda x: x[1], reverse=True)[:3]
            top_merchants_list = [m[0] for m in top_merchants]
            
            cat_breakdown = {}
            for r in records:
                c = r['category']
                cat_breakdown[c] = cat_breakdown.get(c, 0) + (r['amount'] if not math.isnan(r['amount']) else 0)
                
            aggregates = {
                "total_spend_inr": total_inr,
                "total_spend_usd": total_usd,
                "top_merchants": top_merchants_list,
                "anomaly_count": anomaly_count,
                "category_breakdown": cat_breakdown
            }
            
            # 5. LLM Narrative Summary
            summary_result, raw_summary_response, llm_sum_failed = generate_narrative(aggregates)
            
            # 6. Bulk Insert Transactions
            txn_objects = []
            for r in records:
                amount = float(r['amount']) if not math.isnan(r['amount']) else 0.0
                
                txn = Transaction(
                    job_id=job.id,
                    txn_id=r.get('txn_id') if r.get('txn_id') else None,
                    date=r['date'],
                    merchant=r['merchant'][:100],
                    amount=amount,
                    currency=r['currency'][:3],
                    status=r['status'][:10],
                    category=r['category'][:50],
                    account_id=r['account_id'][:20],
                    notes=r.get('notes'),
                    is_anomaly=r.get('is_anomaly', False),
                    anomaly_reasons=r.get('anomaly_reasons'),
                    llm_category=r.get('llm_category'),
                    llm_raw_response=raw_cat_response if r.get('llm_category') else None,
                    llm_failed=llm_cat_failed
                )
                txn_objects.append(txn)
                
            db.bulk_save_objects(txn_objects)
            
            # 7. Insert JobSummary
            job_summary = JobSummary(
                job_id=job.id,
                total_spend_inr=total_inr,
                total_spend_usd=total_usd,
                top_merchants=top_merchants_list,
                anomaly_count=anomaly_count,
                narrative=summary_result.get("narrative"),
                risk_level=summary_result.get("risk_level"),
                llm_raw_response=raw_summary_response
            )
            db.add(job_summary)
            
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Successfully processed job {job_id_str}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to process job {job_id_str}: {str(e)}", exc_info=True)
            job = db.query(Job).filter(Job.id == uuid.UUID(job_id_str)).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
