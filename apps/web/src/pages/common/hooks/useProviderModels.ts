import { useQuery, useQueryClient } from '@tanstack/react-query';
import { settingsApi } from '../../settings/api/SettingsApi';

export const useProviderModels = (provider: string | undefined) => {
  const queryClient = useQueryClient();
  const local = provider === 'huggingface' || provider === 'local';
  const query = useQuery({
    queryKey: ['providerModels', provider],
    queryFn: () => settingsApi.getProviderModels(provider!, false),
    enabled: !!provider && !local,
    staleTime: 5 * 60_000,
  });

  const refresh = async () => {
    if (!provider || local) return;
    const data = await settingsApi.getProviderModels(provider, true);
    queryClient.setQueryData(['providerModels', provider], data);
  };

  return { ...query, refresh };
};
