package edu.institution.lab.jde.agent;

import java.util.Objects;

public class UsageRecord {
    private String pattern;
    private String subject;
    private String funcName;
    private String stack;

    public UsageRecord() {
    }

    public UsageRecord(String pattern, String subject, String funcName, String stack) {
        this.pattern = pattern;
        this.subject = subject;
        this.funcName = funcName;
        this.stack = stack;
    }

    public String getPattern() {
        return pattern;
    }

    public void setPattern(String pattern) {
        this.pattern = pattern;
    }

    public String getSubject() {
        return subject;
    }

    public void setSubject(String subject) {
        this.subject = subject;
    }

    public String getFuncName() {
        return funcName;
    }

    public void setFuncName(String funcName) {
        this.funcName = funcName;
    }

    public String getStack() {
        return stack;
    }

    public void setStack(String stack) {
        this.stack = stack;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        UsageRecord that = (UsageRecord) o;
        return Objects.equals(pattern, that.pattern) && Objects.equals(subject, that.subject) && Objects.equals(funcName, that.funcName) && Objects.equals(stack, that.stack);
    }

    @Override
    public int hashCode() {
        return Objects.hash(pattern, subject, funcName, stack);
    }
}
