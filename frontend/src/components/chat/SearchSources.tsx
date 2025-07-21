import { ExternalLink } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { ScrollArea } from "../ui/scroll-area";

interface SearchSourcesDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  searchData: any;
}

export function SearchSourcesDialog({
  isOpen,
  onOpenChange,
  searchData,
}: SearchSourcesDialogProps) {
  // Handle case with no search data
  if (!searchData || !searchData.results || searchData.results.length === 0) {
    return (
      <Dialog open={isOpen} onOpenChange={onOpenChange}>
        <DialogContent className="bg-[#202222] text-slate-100 border-slate-900">
          <DialogHeader>
            <DialogTitle>Search Sources</DialogTitle>
            <DialogDescription className="text-slate-400">
              No search results available for this response.
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="bg-[#202222] text-slate-100 border-slate-900 max-w-2xl">
        <DialogHeader className="mb-4">
          <DialogTitle className="text-xl">Search Sources</DialogTitle>
          <DialogDescription className="text-slate-400">
            Perplexia used the following web sources to generate its response:
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="h-[60vh] pr-4">
          {searchData.results.map((result: any, index: number) => (
            <div
              key={index}
              className="mb-6 border-b border-slate-800 pb-4 last:border-0"
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-medium text-lg text-sky-400 break-words">
                  {result.title || "Untitled Source"}
                </h3>
                <a
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-400 hover:text-slate-100 flex items-center gap-1 ml-2 shrink-0"
                >
                  <ExternalLink size={16} />
                  <span className="hidden sm:inline">Open</span>
                </a>
              </div>

              {result.url && (
                <div className="text-sm text-slate-500 mb-2 break-all">
                  {result.url}
                </div>
              )}

              {result.content && (
                <div className="text-slate-300 text-sm mt-2 break-words">
                  {result.content}
                </div>
              )}
            </div>
          ))}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
