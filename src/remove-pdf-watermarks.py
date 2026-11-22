# /// script
# requires-python = "~=3.14"
# dependencies = [
#     "marimo~=0.25.2",
#     "matplotlib~=3.11.2",
#     "pillow~=13.0.0",
#     "pymupdf~=2.1",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App()

with app.setup:
    from collections.abc import Iterable
    from dataclasses import dataclass

    from PIL import Image
    from pymupdf import Document, Page, Pixmap

    import marimo as mo
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches


@app.cell
def _(PIL):
    def recurring_images(doc: Document) -> list[int]:
        xrefs = set.intersection(*[
            {i['xref'] for i in page.get_image_info(xrefs=True)}
            for page in doc])
        xrefs.discard(0) # item zero is reserved and must not be used in any way
        return list(xrefs)

    def remove_images(doc: Document, xrefs: list[int]) -> None:
        for page in doc:
            for xref in xrefs:
                page.delete_image(xref)

    def remove_links(doc: Document) -> None:
        for page in doc:
            for link in page.get_links():
                page.delete_link(link)

    def preview_image(page: Page, image_info: dict) -> PIL.Image:
        doc = page.parent
        xref = image_info['xref']
        pixmap = Pixmap(doc, xref)
        if image_info['has-mask']:
            if smask := next((i[1] for i in page.get_images() if i[0] == xref), None):
                pixmap = Pixmap(pixmap, Pixmap(doc, smask))
        return pixmap.pil_image()

    def preview_images(doc: Document, xrefs: Iterable[int]) -> dict[int, PIL.Image]:
        previews = {}
        target_images = set(xrefs)
        for page in doc:
            if len(previews) == len(xrefs):
                break
            for image_info in page.get_image_info(xrefs=True):
                if (xref := image_info['xref']) in target_images and xref not in previews:
                    previews[xref] = preview_image(page, image_info)
        return previews

    def preview_page(page: Page, highlight: Iterable[int] = ()) -> plt.Axes:
        fig, ax = plt.subplots(dpi=300)
        ax.set_axis_off()
        ax.imshow(page.get_pixmap().pil_image())
        target_images = list(highlight)
        for image in page.get_image_info(xrefs=True):
            if image['xref'] in target_images:
                x0, y0, x1, y1 = image['bbox']
                ax.add_patch(patches.Rectangle(
                    xy=(x0, y0), width=x1-x0, height=y1-y0,
                    linewidth=1, facecolor=(1, 0, 0, 0.2)))
        return ax

    return preview_images, recurring_images, remove_images, remove_links


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Удаление водяных знаков для милых барсучков
    """)
    return


@app.cell
def _():
    files = mo.ui.file(label='Выбрать файл', kind="area",
                       filetypes=['.pdf'], max_size=1_000_000_000)
    files
    return (files,)


@app.cell
def _(files, recurring_images):
    mo.stop(not files.value, mo.md(
        'Выберите файл для поиска и удаления водяных знаков'
    ).center())

    file = files.value[0]
    doc = Document(stream=file.contents)
    imgs = recurring_images(doc)
    return doc, file, imgs


@app.cell
def _(doc, file, imgs, preview_images, remove_images, remove_links):
    mo.stop(not imgs, mo.md(
        'Водяных знаков не обнаружено'
    ).callout(kind='warn').center())

    previews = preview_images(doc, imgs)
    remove_images(doc, imgs)
    remove_links(doc)

    mo.vstack([
        mo.md(f'На каждом листе обнаружены и удалены водяные знаки:').callout(kind='success'),
        mo.hstack(previews.values()),
        mo.download(label='Скачать результат', data=doc.tobytes, filename=file.name),
    ], align='center', gap=3)
    return


if __name__ == "__main__":
    app.run()
