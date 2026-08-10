from app.services.retrieval_engine import SimilarBookingRetriever
from datetime import datetime
import pprint

r = SimilarBookingRetriever()
res = r.calculate_representative_price(
    req_date=datetime(2026, 12, 2, 19, 0),
    commercial_slot="24H Night",
    is_weekend=False
)
pprint.pprint(res)
