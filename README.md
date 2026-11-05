# Gerenciador de Etiquetas

Aplicativo desktop Windows para cadastro de produtos, geração de identificadores Code 128 e impressão de etiquetas.

## Instalação e atualização (Windows)

1. Baixe ou mantenha o arquivo `iniciar.bat` e `iniciar.ps1` juntos em uma pasta.
2. Dê dois cliques em `iniciar.bat`.
3. O inicializador consulta a última versão publicada no GitHub Releases, baixa o executável quando necessário e abre o programa.

O computador de destino não precisa ter Python, pip, Git ou bibliotecas instaladas. É necessário Windows com PowerShell e conexão com a internet para baixar/atualizar. Depois do primeiro download, o programa pode abrir sem internet usando a última versão instalada.

## Recursos

- Cadastro de produtos e numeração sequencial independente.
- Identificadores Code 128 no formato `PRODUTO-000001`.
- Banco SQLite local em `%LOCALAPPDATA%\GeradorCodigoBarras\dados.db`.
- Migração automática do banco da versão antiga, preservando os códigos já registrados.
- Modelos iniciais de 50x30, 80x40 e 100x50 mm.
- PDF para etiqueta térmica ou folha A4.
- Confirmação antes de abrir a etiqueta para impressão.
- Histórico e reimpressão sem consumir outro número.

## Impressão

Ao confirmar a impressão, o PDF abre no leitor padrão do Windows. Escolha a impressora instalada e use escala 100% / tamanho real, desativando “Ajustar à página”. Configure o tamanho de papel no driver da impressora térmica.

## Observações

- O banco é local por computador; não há sincronização entre várias máquinas.
- O inicializador atualiza o executável automaticamente a partir do GitHub Releases.
- O executável é produzido pelo GitHub Actions sempre que há atualização na branch `main`.
