package com.example.demo.dto;

import java.util.List;

public class AIResponse {

    private Integer score;
    private List<String> skills;
    private List<String> strengths;
    private List<String> weaknesses;
    private List<String> jobRoles;
    private String experienceLevel;
    public List<String> getStrengths() {
		return strengths;
	}

	public void setStrengths(List<String> strengths) {
		this.strengths = strengths;
	}

	public List<String> getWeaknesses() {
		return weaknesses;
	}

	public void setWeaknesses(List<String> weaknesses) {
		this.weaknesses = weaknesses;
	}

	public List<String> getJobRoles() {
		return jobRoles;
	}

	public void setJobRoles(List<String> jobRoles) {
		this.jobRoles = jobRoles;
	}

	public String getExperienceLevel() {
		return experienceLevel;
	}

	public void setExperienceLevel(String experienceLevel) {
		this.experienceLevel = experienceLevel;
	}

	private String summary;

    public AIResponse() {
        // Default constructor required for Jackson deserialization.
    }

    public Integer getScore() {
        return score;
    }

    public void setScore(Integer score) {
        this.score = score;
    }

    public List<String> getSkills() {
        return skills;
    }

    public void setSkills(List<String> skills) {
        this.skills = skills;
    }

    public String getSummary() {
        return summary;
    }

    public void setSummary(String summary) {
        this.summary = summary;
    }
}