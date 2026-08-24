import { SiteShell } from "@/components/SiteShell";
import { PreferenceQuiz } from "@/components/PreferenceQuiz";

export default function FindPage() {
  return (
    <SiteShell>
      <p className="page-kicker">Personal match</p>
      <h1 className="page-title">Find your place</h1>
      <p className="lede">
        Answer a few preference questions. We re-weight official metrics — no
        chatbot, no invented data.
      </p>
      <PreferenceQuiz />
    </SiteShell>
  );
}
