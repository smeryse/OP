from report_generator.io.json_loader import load_json
from report_generator.io.paths import get_lab_json_path
from report_generator.core.schema import validate_report_data
from report_generator.core.report import generate_report


class ReportBuilder:

    def build_lab_report(self, lab_number: int):
        base_data = load_json("3. data/base_info.json")
        lab_data = load_json(get_lab_json_path(lab_number))

        merged = self._merge(base_data, lab_data)

        validate_report_data(merged)

        return generate_report(merged)

    def _merge(self, base, lab):
        return {**base, **lab}
