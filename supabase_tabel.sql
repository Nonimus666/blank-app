-- Maakt de tabel aan waarin al je taken worden bewaard.
create table if not exists tasks (
  id          text primary key,
  date        date not null,
  title       text not null,
  hours       numeric not null,
  status      text not null default 'open',
  started_at  text,
  finished_at text
);

-- Zet de tabel op slot: alleen jouw app (met de geheime sleutel) komt erbij.
alter table tasks enable row level security;
