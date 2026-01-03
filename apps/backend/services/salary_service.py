from commonlib.salary import SalaryCalculator

class SalaryService:
    @staticmethod
    def calculate_salary(rate, rate_type, hours_x_day, freelance_rate):
        return SalaryCalculator.calculate_salary(
            rate=rate,
            rate_type=rate_type,
            hours_x_day=hours_x_day,
            freelance_rate=freelance_rate
        )
