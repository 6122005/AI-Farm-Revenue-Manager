from app.services.prediction_engine import prediction_engine

# Monkey-patch prediction_engine to print intermediate prices
original_predict = prediction_engine.predict

def hooked_predict(request_data, **kwargs):
    # Just to trace, we'll read the file and insert print statements if we could, but easier to use sed
    pass

