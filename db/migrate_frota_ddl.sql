-- DDL para migração da frota para o Supabase
-- Execute este SQL no Supabase SQL Editor ANTES de rodar migrate_frota.py

-- Tabela de veículos cadastrais
CREATE TABLE IF NOT EXISTS frota_veiculos (
    id           SERIAL PRIMARY KEY,
    modelo       VARCHAR(100) NOT NULL,
    placa        VARCHAR(10)  NOT NULL UNIQUE,
    ano_modelo   VARCHAR(20),
    cod_fipe     VARCHAR(20),
    dt_aquisicao DATE,
    vl_aquisicao NUMERIC(12,2),
    ativo        BOOLEAN      DEFAULT TRUE,
    created_at   TIMESTAMPTZ  DEFAULT NOW()
);

-- Tabela de histórico de valores FIPE mensais
-- mes_ref usa o formato 'JAN/25', 'FEV/25', 'MAI/26', etc.
-- fonte: 'planilha' (importado do Excel) | 'manual' (digitado pelo usuário)
CREATE TABLE IF NOT EXISTS frota_fipe_historico (
    placa        VARCHAR(10)  NOT NULL,
    mes_ref      VARCHAR(10)  NOT NULL,
    valor        NUMERIC(12,2) NOT NULL,
    fonte        VARCHAR(10)  DEFAULT 'planilha',
    atualizado_em DATE,
    created_at   TIMESTAMPTZ  DEFAULT NOW(),
    PRIMARY KEY (placa, mes_ref)
);

-- Índice para facilitar leituras por mês
CREATE INDEX IF NOT EXISTS idx_fipe_hist_mes ON frota_fipe_historico (mes_ref);

-- Row Level Security (RLS) — ajuste conforme suas políticas
-- ALTER TABLE frota_veiculos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE frota_fipe_historico ENABLE ROW LEVEL SECURITY;
