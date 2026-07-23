package com.example.demo.exception;

public class ResumeUploadException extends RuntimeException {

    public ResumeUploadException(String message) {
        super(message);
    }

    public ResumeUploadException(String message, Throwable cause) {
        super(message, cause);
    }
}
