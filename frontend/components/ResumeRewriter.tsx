"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Copy, Check } from "lucide-react";

interface ResumeRewriterProps {
  resumeText: string;
  jobDescription: string;
  missingSkills: string[];
  onRewriteComplete?: (rewrittenResume: string) => void;
}

export function ResumeRewriter({
  resumeText,
  jobDescription,
  missingSkills,
  onRewriteComplete,
}: ResumeRewriterProps) {
  const [loading, setLoading] = useState(false);
  const [rewrittenResume, setRewrittenResume] = useState<string | null>(null);
  const [improvements, setImprovements] = useState<string[]>([]);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRewrite = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/v1/rewrite-resume", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeText,
          job_description: jobDescription,
          missing_skills: missingSkills,
        }),
      });

      if (!response.ok) throw new Error("Failed to rewrite resume");

      const data = await response.json();
      setRewrittenResume(data.rewritten_resume);
      setImprovements(data.key_improvements);
      onRewriteComplete?.(data.rewritten_resume);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (rewrittenResume) {
      navigator.clipboard.writeText(rewrittenResume);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>✏️ Rewrite My Resume</CardTitle>
        <CardDescription>
          AI-powered resume optimization aligned with job requirements
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!rewrittenResume ? (
          <Button onClick={handleRewrite} disabled={loading} className="w-full">
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Rewriting...
              </>
            ) : (
              "Rewrite Resume"
            )}
          </Button>
        ) : (
          <div className="space-y-4">
            {improvements.length > 0 && (
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="font-semibold text-green-900 mb-2">Key Improvements:</p>
                <ul className="space-y-1">
                  {improvements.map((improvement, idx) => (
                    <li key={idx} className="text-sm text-green-800">
                      • {improvement}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="bg-gray-50 p-4 rounded-lg max-h-64 overflow-y-auto">
              <pre className="text-xs whitespace-pre-wrap font-mono">
                {rewrittenResume}
              </pre>
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
