import { cn } from "@/lib/utils";

interface Props {
  body: string;
  senderName: string;
  isMine: boolean;
  createdAt: string;
}

export default function MessageBubble({
  body,
  senderName,
  isMine,
  createdAt,
}: Props) {
  return (
    <div
      className={cn(
        "flex flex-col max-w-[75%]",
        isMine ? "self-end items-end" : "self-start items-start",
      )}
    >
      <p className="text-[10px] uppercase tracking-luxe text-dim mb-1">
        {senderName} · {new Date(createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
      </p>
      <div
        className={cn(
          "px-4 py-2.5 rounded-md whitespace-pre-wrap break-words text-sm",
          isMine
            ? "bg-gold text-black"
            : "bg-panel/80 border border-gold/14 text-ivory",
        )}
      >
        {body}
      </div>
    </div>
  );
}
