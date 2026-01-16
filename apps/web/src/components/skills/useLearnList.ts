import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { skillsApi, type Skill } from '../../api/skills';

export type { Skill };

/**
 * Custom hook to manage the skills learn list
 */
export const useLearnList = () => {
  const queryClient = useQueryClient();

  const { data: learnList = [], isLoading, error: queryError, refetch } = useQuery({
    queryKey: ['skills'],
    queryFn: skillsApi.getSkills,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const error = queryError ? "Failed to load skills from database" : null;

  const createMutation = useMutation({
    mutationFn: skillsApi.createSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
    onError: (err) => {
        console.error("Failed to create skill", err);
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ name, updates }: { name: string; updates: Partial<Skill> }) => 
      skillsApi.updateSkill(name, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
    onError: (err) => {
        console.error("Failed to update skill", err);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: skillsApi.deleteSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
    onError: (err) => {
        console.error("Failed to delete skill", err);
    }
  });

  const toggleSkill = async (skillName: string) => {
    const existing = learnList.find(s => s.name === skillName.trim());
    if (existing && !existing.disabled) {
        // Remove (soft delete)
        await removeSkill(skillName);
    } else if (existing && existing.disabled) {
        // Re-enable
        updateMutation.mutate({ name: skillName, updates: { disabled: false } });
    } else {
        // Create
        createMutation.mutate({
            name: skillName.trim(),
            description: '',
            learningPath: [],
            disabled: false
        });
    }
  };

  const isInLearnList = (skill: string): boolean => {
    const s = learnList.find(s => s.name === skill.trim());
    return !!s && !s.disabled;
  };

  const reorderSkills = async (newList: Skill[]) => {
    // DB doesn't support reordering easily without an 'order' field. 
    // For now, we update local state by updating cache, but this will be reset on refetch.
    queryClient.setQueryData(['skills'], newList);
    console.warn("Reordering not fully supported in Database mode yet.");
  };

  const updateSkill = async (name: string, updates: Partial<Skill>) => {
    updateMutation.mutate({ name, updates });
  };

  const removeSkill = async (skillName: string) => {
     const skill = learnList.find(s => s.name === skillName.trim());
      if (!skill) return;

      const hasContent = (skill.description && skill.description.trim().length > 0) || 
                        (skill.learningPath && skill.learningPath.length > 0);

      if (hasContent) {
         updateMutation.mutate({ name: skillName, updates: { disabled: true } });
      } else {
         deleteMutation.mutate(skillName);
      }
  };

  return { 
      learnList, 
      toggleSkill, 
      reorderSkills, 
      removeSkill, 
      isInLearnList, 
      updateSkill, 
      isLoading, 
      error, 
      fetchSkills: refetch 
  };
};
