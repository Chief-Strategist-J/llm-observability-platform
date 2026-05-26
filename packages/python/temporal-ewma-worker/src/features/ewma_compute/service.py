from shared.types.ewma_types import EwmaRecord


class EwmaService:
    @staticmethod
    def calculate_new_ewma(
        current_value: float, previous_ewma: float, alpha: float = 0.1
    ) -> float:
        return (alpha * current_value) + ((1.0 - alpha) * previous_ewma)

    @staticmethod
    def process_update(
        current_value: float,
        existing_record: EwmaRecord | None,
        global_model_avg: float,
    ) -> EwmaRecord:
        if existing_record is None:
            return EwmaRecord(
                service="",
                model="",
                hour_of_week=0,
                ewma_value=global_model_avg,
                sample_count=1,
                is_cold_start=True,
            )

        new_sample_count = existing_record.sample_count + 1
        new_ewma = EwmaService.calculate_new_ewma(
            current_value, existing_record.ewma_value
        )
        new_is_cold_start = new_sample_count < 7

        return EwmaRecord(
            service=existing_record.service,
            model=existing_record.model,
            hour_of_week=existing_record.hour_of_week,
            ewma_value=new_ewma,
            sample_count=new_sample_count,
            is_cold_start=new_is_cold_start,
        )
