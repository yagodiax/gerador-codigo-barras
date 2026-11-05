# Gerador de Código de Barras

Aplicativo desktop offline para cadastro de produtos, geração sequencial de códigos de barras Code 128 e impressão de etiquetas em PDF com dimensões físicas em milímetros.

## Estado atual

Estrutura inicial do projeto. O cadastro local e a numeração independente por produto serão implementados em Python + Tkinter + SQLite. A geração de PDF e o empacotamento portátil serão adicionados nas próximas etapas.

## Requisitos de desenvolvimento

- Python 3.11 ou superior
- Windows 10/11

## Executar

```powershell
python main.py
```

O banco de dados será armazenado em `%LOCALAPPDATA%\\GeradorCodigoBarras\\dados.db`.

## Distribuição

A versão final será empacotada para Windows, sem exigir instalação manual de Python ou dependências no computador de destino.
