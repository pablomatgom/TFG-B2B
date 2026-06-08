"use client";

import { XMarkIcon } from "@heroicons/react/24/outline";
import SimpleBarList from "@/components/dashboard/SimpleBarList";

export interface ModalData {
  title:    string;
  subtitle: string;
  data:     { name: string; value: number }[];
  suffix:   string;
  color:    string;
}

interface RankingModalProps {
  modal:   ModalData | null;
  onClose: () => void;
}

export default function RankingModal({ modal, onClose }: RankingModalProps) {
  if (!modal) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-md bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 px-6 pt-5 pb-4 border-b border-gray-100">
          <div>
            <p className="text-gray-900 font-bold text-base">{modal.title}</p>
            <p className="text-gray-400 text-xs mt-0.5">{modal.subtitle}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors shrink-0"
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        </div>

        {/* List */}
        <div className="px-6 py-5 max-h-[60vh] overflow-y-auto">
          <SimpleBarList data={modal.data} suffix={modal.suffix} color={modal.color} />
        </div>

        {/* Footer */}
        <div className="px-6 pb-4 text-[10px] text-gray-400 text-right font-mono">
          {modal.data.length} entidades
        </div>
      </div>
    </div>
  );
}