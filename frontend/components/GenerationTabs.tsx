"use client";

import { useState } from "react";
import { ResumeRewriter } from "@/components/ResumeRewriter";
import { CoverLetterGenerator } from "@/components/CoverLetterGenerator";
import { PDFExporter } from "@/components/PDFExporter";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface GenerationTabsProps {
  resumeText: string;
  jobDescription: string;
  missingSkills: string[];
  matchScore: number;
  candidateName: string;
  jobTitle: string;
}

export function GenerationTabs({
  resumeText,
  jobDescription,
  missingSkills,
  matchScore,
  candidateName,
  jobTitle,
}: GenerationTabsProps) {
  const [rewrittenResume, setRewrittenResume] = useState<string>("");
  const [generatedCoverLetter, setGeneratedCoverLetter] = useState<string>("");

  return (
    <Tabs defaultValue="rewrite" className="w-full">
      <TabsList className="grid w-full grid-cols-3">
        <TabsTrigger value="rewrite">✏️ Rewrite Resume</TabsTrigger>
        <TabsTrigger value="cover">📝 Cover Letter</TabsTrigger>
        <TabsTrigger value="export">⬇️ Export PDF</TabsTrigger>
      </TabsList>

      <TabsContent value="rewrite" className="mt-6">
        <ResumeRewriter
          resumeText={resumeText}
          jobDescription={jobDescription}
          missingSkills={missingSkills}
          onRewriteComplete={setRewrittenResume}
        />
      </TabsContent>

      <TabsContent value="cover" className="mt-6">
        <CoverLetterGenerator
          candidateName={candidateName}
          resumeText={resumeText}
          jobDescription={jobDescription}
          matchScore={matchScore}
          onGenerateComplete={setGeneratedCoverLetter}
        />
      </TabsContent>

      <TabsContent value="export" className="mt-6">
        <PDFExporter
          resumeText={rewrittenResume || resumeText}
          coverLetterText={generatedCoverLetter}
          candidateName={candidateName}
          jobTitle={jobTitle}
        />
      </TabsContent>
    </Tabs>
  );
}
