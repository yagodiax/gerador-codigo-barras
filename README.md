# Gerenciador de Etiquetas

Aplicativo desktop Windows para cadastro de produtos, geração de identificadores Code 128 e impressão de etiquetas em PDF.

## Executar
Dê dois cliques em `iniciar.bat`. Se Python 3.13 não estiver instalado, o inicializador tenta instalá-lo via WinGet. A primeira execução exige internet para instalar Python/dependências.

## Recursos
- Cadastro de produtos e numeração sequencial independente.
- Identificadores exclusivos no formato `PRODUTO-000001`.
- Banco SQLite local em `%LOCALAPPDATA%\GeradorCodigoBarras\dados.db`.
- Modelos iniciais de 50x30, 80x40 e 100x50 mm.
- PDF em tamanho físico para etiqueta térmica ou distribuição básica em folha A4.
- Seleção de item no histórico para reimpressão sem consumir outro número.

## Impressão
O PDF abre no leitor padrão do Windows. Escolha a impressora instalada. Para manter as dimensões, use escala 100% / tamanho real e desative “Ajustar à página”. Na impressora térmica, configure o papel com a mesma dimensão da etiqueta.

## Limitações desta versão
A impressão é feita pelo leitor PDF e depende do driver da impressora. A distribuição A4 está em versão básica. O banco é local por computador; não há sincronização multiusuário. Teste alinhamento e leitura dos códigos antes de uso operacional.
