from temporalio import activity

@activity.defn
async def collect_and_route_otlp_activity(otlp_data):
    return otlp_data

if __name__ == "__main__":
    print(collect_and_route_otlp_activity.__name__)
