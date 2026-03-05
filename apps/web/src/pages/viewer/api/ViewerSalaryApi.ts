import apiClient from "../../common/api/ApiClient";

export interface SalaryCalculationRequest {
  rate: number;
  rate_type: "Hourly" | "Daily";
  hours_x_day: number;
  freelance_rate: number;
}

export interface SalaryCalculationResponse {
  gross_year: string;
  parsed_equation: string;
  year_tax: string;
  year_tax_equation: string;
  net_year: string;
  net_month: string;
  freelance_tax: string;
}

const handleRequest = async <T>(
  request: Promise<{ data: T }>,
  errorMessage: string
): Promise<T> => {
  try {
    const response = await request;
    return response.data;
  } catch (error) {
    throw new Error(
      `${errorMessage}: ${
        error instanceof Error ? error.message : String(error)
      }`
    );
  }
};

export const salaryApi = {
  calculate: async (
    data: SalaryCalculationRequest
  ): Promise<SalaryCalculationResponse> => {
    return handleRequest(
      apiClient.post<SalaryCalculationResponse>("/salary/calculate", data),
      "Error calculating salary"
    );
  },
};
