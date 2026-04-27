-- DB_Manager 자동 업데이트용 릴리즈 테이블
-- 적용: psql -U dbmanager -d dbmanager -f 02_app_releases.sql

CREATE TABLE IF NOT EXISTS app_releases (
    id                    SERIAL PRIMARY KEY,
    version               TEXT NOT NULL UNIQUE,
    release_date          TIMESTAMP NOT NULL DEFAULT NOW(),
    download_url          TEXT NOT NULL,
    release_notes         TEXT,
    is_critical           BOOLEAN NOT NULL DEFAULT FALSE,
    min_compatible_version TEXT
);

CREATE INDEX IF NOT EXISTS idx_app_releases_date
    ON app_releases (release_date DESC);

-- 샘플 (첫 등록 시 주석 해제 후 version/url 수정)
-- INSERT INTO app_releases (version, download_url, release_notes, is_critical)
-- VALUES (
--     '1.5.0',
--     '\\fileserver\share\DB_Manager\v1.5.0\DB_Manager.exe',
--     '## v1.5.0\n- F4 검색 Prev/Next 네비게이션\n- F5 서버폴더 접근 보강\n- F13 자동 업데이트 체크\n- F14 리포트 템플릿 커스터마이징',
--     FALSE
-- );
