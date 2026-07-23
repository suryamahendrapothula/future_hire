package com.example.demo.service;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.example.demo.dto.ResumeAnalysis;

@Service
public class ResumeAnalysisServiceImpl implements ResumeAnalysisService {
    private static final Logger logger =
        LoggerFactory.getLogger(ResumeAnalysisServiceImpl.class);

    @Override
    public ResumeAnalysis analyze(String resumeText) {

        ResumeAnalysis analysis = new ResumeAnalysis();

        List<String> detectedSkills = new ArrayList<>();

        try {

            InputStream inputStream =
                    getClass().getClassLoader().getResourceAsStream("skills.txt");

            BufferedReader reader =
                    new BufferedReader(new InputStreamReader(inputStream));

            String skill;

            while ((skill = reader.readLine()) != null) {

                if (resumeText.toLowerCase().contains(skill.toLowerCase())) {
                    detectedSkills.add(skill);
                }

            }

            reader.close();

        } catch (Exception e) {
            logger.error("Error while analyzing resume.", e);
        }

        analysis.setSkills(detectedSkills);

        return analysis;
    }
    

}