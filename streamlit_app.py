from __future__ import annotations

import streamlit as st

from converter import ConversionError, convert_csv_bytes


st.set_page_config(
    page_title="CAS-Interessenten CRM-Konverter",
    page_icon=":material/sync_alt:",
    layout="wide",
)


def main() -> None:
    st.title("CAS-Interessenten CRM-Konverter")
    st.caption("CSV hochladen, Mapping prüfen, CRM-Importdatei herunterladen.")

    with st.container(border=True):
        st.subheader("Upload")
        uploaded_file = st.file_uploader(
            "CAS-Interessenten-CSV auswählen",
            type=["csv"],
            help="Die Datei muss Semikolon-getrennt sein und die Spalten aus dem Webseitenformular enthalten.",
        )

    if uploaded_file is None:
        st.info("Bitte lade eine CAS-Interessenten-CSV hoch.")
        return

    try:
        result = convert_csv_bytes(uploaded_file.getvalue())
    except ConversionError as error:
        st.error(str(error))
        return

    st.success("Datei erfolgreich konvertiert.")

    metric_columns = st.columns(4)
    metric_columns[0].metric("Zeilen", result.stats.row_count)
    metric_columns[1].metric(
        "Vornamen ergänzt", result.stats.firstnames_filled_from_vorname
    )
    metric_columns[2].metric(
        "Nachnamen ergänzt", result.stats.lastnames_filled_from_nachname
    )
    metric_columns[3].metric("N.N.-Fallbacks", result.stats.lastnames_filled_with_nn)

    with st.container(border=True):
        st.subheader("Vorschau")
        st.dataframe(result.rows[:50], hide_index=True, use_container_width=True)
        st.caption("Angezeigt werden maximal die ersten 50 konvertierten Zeilen.")

    st.download_button(
        "Konvertierte CSV herunterladen",
        data=result.csv_bytes,
        file_name="cas_interessenten_crm_import.csv",
        mime="text/csv",
        type="primary",
        icon=":material/download:",
    )


if __name__ == "__main__":
    main()
