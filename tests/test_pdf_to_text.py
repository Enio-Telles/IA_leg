import pytest
from unittest.mock import MagicMock, patch
from etl.pdf_to_text import extrair_texto_pdf

def test_extrair_texto_pdf_sucesso():
    # Arrange
    caminho_pdf = "fake_document.pdf"

    # Mocking the document object
    mock_doc = MagicMock()

    # Mocking pages
    mock_page_1 = MagicMock()
    # Simulates text with multiple newlines to test the regex \n{3,} -> \n\n
    mock_page_1.get_text.return_value = "Page 1 Text\n\n\n\n\nExtra lines.\n"

    mock_page_2 = MagicMock()
    mock_page_2.get_text.return_value = "Page 2 Text\n\nSome more text."

    # doc acts as an iterator over pages
    mock_doc.__iter__.return_value = iter([mock_page_1, mock_page_2])

    with patch("etl.pdf_to_text.fitz.open", return_value=mock_doc) as mock_fitz_open:
        # Act
        resultado = extrair_texto_pdf(caminho_pdf)

        # Assert
        mock_fitz_open.assert_called_once_with(caminho_pdf)
        mock_doc.close.assert_called_once()

        # Check that multiple newlines are replaced and the pages are joined with \n\n
        expected_page_1 = "Page 1 Text\n\nExtra lines."
        expected_page_2 = "Page 2 Text\n\nSome more text."

        assert resultado == f"{expected_page_1}\n\n{expected_page_2}"

def test_extrair_texto_pdf_erro(capsys):
    # Arrange
    caminho_pdf = "invalid_document.pdf"

    with patch("etl.pdf_to_text.fitz.open", side_effect=Exception("Simulated error")) as mock_fitz_open:
        # Act
        resultado = extrair_texto_pdf(caminho_pdf)

        # Assert
        mock_fitz_open.assert_called_once_with(caminho_pdf)
        assert resultado == ""

        # Verify the print statement happened
        captured = capsys.readouterr()
        assert f"Erro ao ler PDF {caminho_pdf}: Simulated error" in captured.out
