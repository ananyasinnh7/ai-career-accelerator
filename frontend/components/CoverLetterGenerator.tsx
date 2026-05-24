"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Loader2, Copy, Check } from "lucide-react";

interface CoverLetterGeneratorProps {
  candidateName: string;
  resumeText: string;
  jobDescription: string;
  matchScore: number;
  onGenerateComplete?: (coverLetter: string) => void;
}

export function CoverLetterGenerator({
  candidateName,
  resumeText,
  jobDescription,
  matchScore,
  onGenerateComplete,
}: CoverLetterGeneratorProps) {
  const [loading, setLoading] = useState(false);
  const [coverLetter, setCoverLetter] = useState<string | null>(null);
  const [tone, setTone] = useState<string>("professional");
  const [companyName, setCompanyName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!companyName || !jobTitle) {
      setError("Please enter company name and job title");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/v1/generate-cover-letter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_name: candidateName,
          company_name: companyName,
          job_title: jobTitle,
          resume_text: resumeText,
          job_description: jobDescription,
          match_score: matchScore,
        }),
      });

      if (!response.ok) throw new Error("Failed to generate cover letter");

      const data = await response.json();
      setCoverLetter(data.cover_letter);
      setTone(data.tone);
      onGenerateComplete?.(data.cover_letter);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (coverLetter) {
      navigator.clipboard.writeText(coverLetter);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>📝 Generate Cover Letter</CardTitle>
        <CardDescription>
          AI-powered personalized cover letter for your application
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!coverLetter ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                placeholder="Company name"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
              />
              <Input
                placeholder="Job title"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
              />
            </div>
            <Button onClick={handleGenerate} disabled={loading} className="w-full">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                "Generate Cover Letter"
              )}
            </Button>
          </>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">
                Tone: <span className="font-semibold capitalize">{tone}</span>
              </p>
            </div>

            <div className="bg-blue-50 p-6 rounded-lg max-h-64 overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed">
              {coverLetter}
            </div>

            <Button
              onClick={copyToClipboard}
              variant="outline"
              className="w-full"
            >
              {copied ? (
                <>
                  <Check className="mr-2 h-4 w-4" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="mr-2 h-4 w-4" />
                  Copy to Clipboard
                </>
              )}
            </Button>
          </div>
        )}

        {error && <p className="text-sm text-red-500">{error}</p>}
      </CardContent>
    </Card>
  );
}
