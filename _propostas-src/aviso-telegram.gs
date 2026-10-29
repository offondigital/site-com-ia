/**
 * Aviso de proposta no Telegram — projeto Apps Script SEPARADO do CRM.
 *
 * Publicar como: Implantar > Nova implantação > App da Web
 *   Executar como: Eu | Quem pode acessar: Qualquer pessoa
 *
 * Propriedades do script (Configurações do projeto > Propriedades do script):
 *   TELEGRAM_TOKEN  token do bot (@BotFather)
 *   TELEGRAM_CHAT   seu chat id (número)
 *
 * O token fica só aqui; a página pública da proposta nunca o vê.
 * A página chama este endereço com ?e=<evento>&p=<slug>&c=<cliente>.
 */
const EVENTOS = {
  aberta: '👀 Proposta VISUALIZADA',
  rolou50: '📖 Está lendo (50% da proposta)',
  rolou100: '✅ Leu até o fim',
  cta: '🔥 Clicou no botão de WhatsApp',
};
const SLUG_OK = /^[a-z0-9-]{3,80}$/;

function doGet(e) {
  const p = (e && e.parameter) || {};
  const evento = String(p.e || '');
  const slug = String(p.p || '');
  if (!EVENTOS[evento] || !SLUG_OK.test(slug)) return saida_('ignorado');

  // Cada evento por proposta avisa no máximo 1x a cada 30 min (evita spam e duplicidade).
  const cache = CacheService.getScriptCache();
  const chave = 'av_' + slug + '_' + evento;
  if (cache.get(chave)) return saida_('repetido');
  cache.put(chave, '1', 1800);

  const cliente = String(p.c || slug).replace(/[^\p{L}\p{N} .\-]/gu, '').slice(0, 60);
  const quando = Utilities.formatDate(new Date(), 'America/Sao_Paulo', 'dd/MM HH:mm');
  const texto = EVENTOS[evento] + '\n' + cliente + '\n' + quando +
    '\ninovaseo.com.br/propostas/' + slug + '.html';

  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('TELEGRAM_TOKEN');
  const chat = props.getProperty('TELEGRAM_CHAT');
  if (!token || !chat) return saida_('sem-config');

  UrlFetchApp.fetch('https://api.telegram.org/bot' + token + '/sendMessage', {
    method: 'post',
    payload: { chat_id: chat, text: texto, disable_web_page_preview: 'true' },
    muteHttpExceptions: true,
  });
  return saida_('ok');
}

function saida_(s) {
  return ContentService.createTextOutput(s);
}

/** Rode uma vez no editor para testar o aviso (depois de salvar as propriedades). */
function testar() {
  const r = doGet({ parameter: { e: 'aberta', p: 'teste-00-00-0000', c: 'Teste' } });
  Logger.log(r.getContent());
}
