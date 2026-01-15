import Modal from "./Modal";

interface ConfirmDeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  itemType: "conspect" | "test";
}

const ConfirmDeleteModal = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  itemType,
}: ConfirmDeleteModalProps) => {
  const itemLabel = itemType === "conspect" ? "конспект" : "тест";

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Підтвердження видалення" size="md">
      <div className="space-y-6">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-red-100">
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#DC2626"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M3 6h18" />
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
              <line x1="10" y1="11" x2="10" y2="17" />
              <line x1="14" y1="11" x2="14" y2="17" />
            </svg>
          </div>
          <p className="text-base font-semibold text-slate-900">
            Видалити {itemLabel} "{title}"?
          </p>
          <p className="mt-2 text-sm text-slate-600">
            Цю дію неможливо скасувати. {itemType === "conspect" ? "Конспект" : "Тест"} буде
            видалено для всіх учнів класу.
          </p>
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 rounded-xl border border-slate-200 bg-white py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            Скасувати
          </button>
          <button
            type="button"
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className="flex-1 rounded-xl bg-red-600 py-3 text-sm font-semibold text-white transition hover:bg-red-700"
          >
            Видалити
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default ConfirmDeleteModal;
