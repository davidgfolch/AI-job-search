import { useQuery } from '@tanstack/react-query';
import { getModalityValues } from '../api/DdlApi';

export const useModalityValues = () => {
  return useQuery({
    queryKey: ['modalityValues'],
    queryFn: () => getModalityValues(),
    staleTime: Infinity,
  });
};
