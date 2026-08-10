from app.services.slot_relationship_engine import slot_relationship_engine
ratio, lvl = slot_relationship_engine.get_conversion_ratio("12H Day", "24H Night", 4)
print(f"Ratio 24H Night -> 12H Day: {ratio}")
