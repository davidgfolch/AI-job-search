import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { skillsApi, type Skill } from '../api/SkillsManagerApi';
import { normalizeName } from '../utils/skillUtils';

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

  const skillExists = (skillName: string): Skill | undefined => {
    const search = normalizeName(skillName);
    return learnList.find(s => normalizeName(s.name) === search);
  };

  const toggleSkill = async (skillName: string) => {
    const skill = skillExists(skillName);
    if (skill && !skill.disabled) {
        // Remove (soft delete)
        await removeSkill(skillName);
    } else if (skill && skill.disabled) {
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

  const isInLearnList = (skillName: string): boolean => {
    const skill = skillExists(skillName);
    return !!skill && !skill.disabled;
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
     const skill = skillExists(skillName);
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
      skillExists, 
      isLoading, 
      error, 
      fetchSkills: refetch,
      saveSkill: (skill: Skill) => {
        if (skillExists(skill.name)) {
             const { name, ...updates } = skill;
             updateMutation.mutate({ name, updates });
        } else {
             createMutation.mutate(skill);
        }
      }
  };
};
