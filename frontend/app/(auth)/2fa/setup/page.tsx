import { redirect } from "next/navigation";
import { safeServerFetch, serverFetch } from "@/lib/api/server";
import { getCurrentUser } from "@/lib/auth/server";
import TotpVerifyForm from "./TotpVerifyForm";

interface SetupResponse {
  provisioning_uri: string;
  secret: string;
}

export default async function TotpSetupPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/2fa/setup");

  let setup: SetupResponse | null = null;
  try {
    setup = await serverFetch<SetupResponse>(
      "/api/v1/auth/2fa/totp/setup/",
      { method: "POST" },
      { auth: true },
    );
  } catch {
    setup = await safeServerFetch<SetupResponse>(
      "/api/v1/auth/2fa/totp/setup/",
      { method: "POST" },
      { auth: true },
    );
  }

  if (!setup) {
    return (
      <div className="text-center">
        <div className="ey mb-5">2FA setup</div>
        <h1 className="font-serif font-light text-ivory text-3xl leading-tight">
          Couldn't start setup.
        </h1>
        <p className="text-mist mt-4 leading-relaxed">
          Try again in a moment, or contact support if it persists.
        </p>
      </div>
    );
  }

  const qrSrc = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&margin=4&data=${encodeURIComponent(setup.provisioning_uri)}`;

  return (
    <div>
      <div className="mb-8">
        <div className="ey mb-3">Two-factor</div>
        <h1 className="font-serif font-light text-ivory text-3xl leading-tight">
          Set up authenticator
        </h1>
        <p className="text-mist text-sm mt-3 leading-relaxed">
          Scan the QR with Authy, 1Password, Google Authenticator, or any TOTP
          app. Then enter the 6-digit code below to confirm.
        </p>
      </div>

      <div className="bg-deep border border-gold/22 p-6 mb-6 flex flex-col items-center">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={qrSrc}
          alt="QR code for authenticator app"
          width={220}
          height={220}
          className="bg-white p-2"
        />
        <p className="text-[11px] uppercase tracking-luxe text-mist mt-5 mb-2">
          Or enter manually
        </p>
        <code className="font-mono text-gold text-sm break-all text-center bg-warm px-3 py-2 border border-gold/14 max-w-xs">
          {setup.secret}
        </code>
      </div>

      <TotpVerifyForm />
    </div>
  );
}
