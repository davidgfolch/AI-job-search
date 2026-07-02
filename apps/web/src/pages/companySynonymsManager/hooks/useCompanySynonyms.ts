import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { companySynonymsApi, type SynonymGroup } from '../api/CompanySynonymsManagerApi';

export function useCompanySynonyms() {
  const queryClient = useQueryClient();

  const { data: groups = [], isLoading, error } = useQuery<SynonymGroup[]>({
    queryKey: ['companySynonyms'],
    queryFn: companySynonymsApi.listGroups,
    staleTime: 5 * 60 * 1000,
  });

  const createGroupMutation = useMutation({
    mutationFn: (names: string[]) => companySynonymsApi.createGroup(names),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['companySynonyms'] }),
  });

  const addToGroupMutation = useMutation({
    mutationFn: ({ groupId, name }: { groupId: number; name: string }) =>
      companySynonymsApi.addToGroup(groupId, name),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['companySynonyms'] }),
  });

  const removeNameMutation = useMutation({
    mutationFn: (name: string) => companySynonymsApi.removeName(name),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['companySynonyms'] }),
  });

  return {
    groups,
    isLoading,
    error,
    createGroup: createGroupMutation.mutateAsync,
    addToGroup: addToGroupMutation.mutateAsync,
    removeName: removeNameMutation.mutateAsync,
  };
}
