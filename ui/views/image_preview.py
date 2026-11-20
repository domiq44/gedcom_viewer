"""Mixin de prévisualisation d'images et de PDF."""

import logging
import os
from typing import Any

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None  # type: ignore[assignment]
    ImageTk = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

MAX_PREVIEW_BYTES = 25 * 1024 * 1024

IMAGE_PREVIEW_EXTENSIONS = frozenset(
    {
        ".bmp",
        ".gif",
        ".jpeg",
        ".jpg",
        ".pbm",
        ".pgm",
        ".png",
        ".pnm",
        ".ppm",
        ".tif",
        ".tiff",
        ".webp",
    }
)
PDF_PREVIEW_EXTENSIONS = frozenset({".pdf"})
SUPPORTED_PREVIEW_EXTENSIONS = IMAGE_PREVIEW_EXTENSIONS | PDF_PREVIEW_EXTENSIONS


class ImagePreviewMixin:
    """Partage le chargement sécurisé des aperçus d'images locales."""

    translator: Any

    def _init_image_preview(self) -> None:
        """Initialise l'état de prévisualisation."""
        self.base_path: str | None = None
        self._preview_photo: Any = None
        self.preview_label: Any = None

    def set_base_path(self, base_path: str | None) -> None:
        """Définit le répertoire de base des images."""
        self.base_path = base_path if base_path and os.path.isdir(base_path) else None

    @staticmethod
    def _render_pdf_preview(file_path: str) -> Any:
        """Rend une prévisualisation PDF."""
        if pdfium is None:
            return None
        document = pdfium.PdfDocument(file_path)
        try:
            if len(document) == 0:
                return None
            page = document[0]
            try:
                page_width, page_height = page.get_size()
                scale = min(640 / page_width, 480 / page_height, 1.5)
                bitmap = page.render(scale=scale)
                try:
                    return bitmap.to_pil().convert("RGB")
                finally:
                    bitmap.close()
            finally:
                page.close()
        finally:
            document.close()

    @staticmethod
    def _is_within_base(path: str, base_path: str) -> bool:
        """Indique si un chemin résolu reste dans le répertoire de base."""
        try:
            common = os.path.commonpath([path, base_path])
        except ValueError:
            return False
        return os.path.normcase(common) == os.path.normcase(base_path)

    def _is_acceptable_file(self, resolved: str) -> bool:
        """Vérifie qu'un fichier résolu est utilisable pour l'aperçu."""
        if not os.path.isfile(resolved):
            return False
        try:
            return os.path.getsize(resolved) <= MAX_PREVIEW_BYTES
        except OSError:
            return False

    def _resolve_preview_path(self, file_path: str | None) -> str | None:
        """Résout un fichier d'aperçu.

        Essaie, dans l'ordre :
        1. Le chemin tel quel (en particulier les chemins absolus explicites)
        2. Le chemin résolu par rapport à ``base_path`` (si défini)

        Le fichier doit exister, avoir une extension supportée et ne pas
        dépasser la taille maximale.
        """
        if not file_path:
            return None
        if os.path.splitext(file_path)[1].lower() not in SUPPORTED_PREVIEW_EXTENSIONS:
            return None

        # 1. Chemin tel quel (notamment les chemins absolus explicites)
        resolved = os.path.realpath(file_path)
        if self._is_acceptable_file(resolved):
            return resolved

        # 2. Chemin relatif résolu par rapport à base_path
        if self.base_path:
            base_path = os.path.realpath(self.base_path)
            candidate = os.path.join(base_path, file_path)
            resolved = os.path.realpath(candidate)
            if self._is_within_base(resolved, base_path) and self._is_acceptable_file(
                resolved
            ):
                return resolved

        return None

    def _show_preview_placeholder(self) -> None:
        """Affiche l'état d'aperçu indisponible."""
        logger.info("Prévisualisation non disponible")
        self.preview_label.configure(
            text=self.translator.get("view.preview_unavailable"), image=""
        )
        self.preview_label.image = None
        self._preview_photo = None

    def _show_preview(self, file_path: str | None) -> None:
        """Affiche l'aperçu d'un fichier image ou PDF."""
        resolved = self._resolve_preview_path(file_path)
        if resolved is None:
            self._show_preview_placeholder()
            return

        logger.info("Tentative d'affichage de la prévisualisation")
        if Image is None or ImageTk is None:
            self._show_preview_placeholder()
            return
        try:
            if os.path.splitext(resolved)[1].lower() == ".pdf":
                image = self._render_pdf_preview(resolved)
                if image is None:
                    self._show_preview_placeholder()
                    return
            else:
                with Image.open(resolved) as source_image:
                    image = source_image.convert("RGB")
            image.thumbnail((640, 480))
            photo = ImageTk.PhotoImage(image)
        except Exception as exc:
            logger.warning("Échec du chargement de l'image (%s)", type(exc).__name__)
            self._show_preview_placeholder()
            return

        self._preview_photo = photo
        self.preview_label.image = photo
        self.preview_label.configure(text="", image=photo)
