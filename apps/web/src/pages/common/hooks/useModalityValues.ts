import { useQuery } from '@tanstack/react-query';
import { jobsApi } from '../../viewer/api/ViewerApi';

export const useModalityValues = () => {
  return useQuery({
    queryKey: ['modalityValues'],
    queryFn: () => jobsApi.getModalityValues(),
    staleTime: Infinity,
  });
};
