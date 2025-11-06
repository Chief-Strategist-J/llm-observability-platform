from temporalio import activity
from ingest.otlp_from_apps.agents.otlp_receiver_setup import OTLPReceiverSetup

@activity.defn
async def enable_otlp_receiver_activity(template_path, service_name, otlp_endpoint):
    s = OTLPReceiverSetup(template_path, service_name, otlp_endpoint)
    return s.write_temp_config()

if __name__ == "__main__":
    print(enable_otlp_receiver_activity.__name__)
