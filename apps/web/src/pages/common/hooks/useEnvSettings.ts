import { useQuery, useQueryClient } from '@tanstack/react-query';
import { settingsApi } from '../../settings/api/SettingsApi';

export const useEnvSettings = () => {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['envSettings'],
    queryFn: () => settingsApi.getEnvSettings(),
    staleTime: Infinity,
  });

  const updateSettings = async (key: string, value: string) => {
    await settingsApi.updateEnvSetting(key, value);
    queryClient.invalidateQueries({ queryKey: ['envSettings'] });
  };

  const updateSettingsBulk = async (updates: Record<string, string>) => {
    const result = await settingsApi.updateEnvSettingsBulk(updates);
    queryClient.invalidateQueries({ queryKey: ['envSettings'] });
    return result;
  };

  return { ...query, updateSettings, updateSettingsBulk };
};
