"""
Checklist AutoFill Dialog
Reviewer UI for previewing and confirming QC value auto-fill into checklist Excel.
"""

import logging
import threading
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

import customtkinter as ctk

logger = logging.getLogger(__name__)

# Confidence-source colour map (hex background → Treeview tag)
_SOURCE_COLORS = {
    'explicit': '#E8F5E9',
    'learned':  '#E8F5E9',
    'exact':    '#E8F5E9',
    'fuzzy':    '#FFF8E1',
    'unit_hint':'#FFF8E1',
    'unmapped': '#FFEBEE',
}


class ChecklistAutoFillDialog(ctk.CTkToplevel):
    """Reviewer dialog: preview mapping results, confirm auto-fill."""

    def __init__(self, parent,
                 excel_path: str,
                 qc_report: dict,
                 sync_manager=None,
                 model: str = '',
                 profile_name: str = ''):
        super().__init__(parent)

        self.excel_path = excel_path
        self.qc_report = qc_report
        self.sync_manager = sync_manager
        self.model = model
        self.profile_name = profile_name

        # Options
        self._dry_run_var = ctk.BooleanVar(value=True)
        self._fill_meta_var = ctk.BooleanVar(value=False)
        self._write_dbkey_var = ctk.BooleanVar(value=False)
        self._threshold_var = ctk.StringVar(value='0.80')

        # State
        self._map_results = []   # List[MapResult]
        self._report = None      # AutoFillReport after run

        self.title("Industrial Checklist 자동 기입")
        self.geometry("1100x720")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)

        self._build_ui()
        self._run_mapping_async()

    # -----------------------------------------------------------------------
    # UI Construction
    # -----------------------------------------------------------------------

    def _build_ui(self):
        # === Header ===
        hdr = ctk.CTkFrame(self, fg_color='transparent')
        hdr.pack(fill='x', padx=20, pady=(15, 5))

        ctk.CTkLabel(hdr, text='Industrial Checklist 자동 기입',
                     font=('Segoe UI', 18, 'bold')).pack(anchor='w')
        excel_name = Path(self.excel_path).name
        ctk.CTkLabel(hdr,
                     text=f'File: {excel_name}  |  Profile: {self.profile_name}  |  Model: {self.model}',
                     font=('Segoe UI', 11), text_color='#888888').pack(anchor='w', pady=(2, 0))

        # === Stats bar ===
        self._stats_frame = ctk.CTkFrame(self)
        self._stats_frame.pack(fill='x', padx=20, pady=8)
        self._stat_labels: dict = {}
        for i, (key, label, color) in enumerate([
            ('filled',   'Auto-fill',  '#27ae60'),
            ('learned',  'Learned',    '#4a9eff'),
            ('fuzzy',    'Fuzzy',      '#f39c12'),
            ('unmapped', 'Unmapped',   '#e74c3c'),
            ('protected','Protected',  '#888888'),
        ]):
            col_f = ctk.CTkFrame(self._stats_frame, fg_color='transparent')
            col_f.grid(row=0, column=i, padx=22, pady=8)
            val_lbl = ctk.CTkLabel(col_f, text='-',
                                   font=('Segoe UI', 22, 'bold'), text_color=color)
            val_lbl.pack()
            ctk.CTkLabel(col_f, text=label,
                         font=('Segoe UI', 10), text_color='#aaaaaa').pack()
            self._stat_labels[key] = val_lbl

        # === Options row ===
        opt_frame = ctk.CTkFrame(self, fg_color='transparent')
        opt_frame.pack(fill='x', padx=20, pady=(2, 6))

        ctk.CTkCheckBox(opt_frame, text='Dry-run (미리보기만)',
                        variable=self._dry_run_var,
                        font=('Segoe UI', 12)).pack(side='left', padx=(0, 16))
        ctk.CTkCheckBox(opt_frame, text='메타데이터 자동 채우기 (Last 시트)',
                        variable=self._fill_meta_var,
                        font=('Segoe UI', 12)).pack(side='left', padx=(0, 16))
        ctk.CTkCheckBox(opt_frame, text='M열(DB_Key) 채우기',
                        variable=self._write_dbkey_var,
                        font=('Segoe UI', 12)).pack(side='left', padx=(0, 16))

        ctk.CTkLabel(opt_frame, text='신뢰도 임계값:',
                     font=('Segoe UI', 12)).pack(side='left')
        ctk.CTkEntry(opt_frame, textvariable=self._threshold_var,
                     width=55, font=('Segoe UI', 12)).pack(side='left', padx=4)

        # === Bottom action buttons (pack before table) ===
        btn_frame = ctk.CTkFrame(self, fg_color='transparent')
        btn_frame.pack(fill='x', padx=20, pady=(0, 14), side='bottom')

        self._btn_dryrun = ctk.CTkButton(
            btn_frame, text='Dry-run 미리보기', command=self._on_dryrun,
            font=('Segoe UI', 13), fg_color='#2196F3', hover_color='#1976D2',
            width=160, height=38)
        self._btn_dryrun.pack(side='left', padx=(0, 10))

        self._btn_confirm = ctk.CTkButton(
            btn_frame, text='확정 기입', command=self._on_confirm,
            font=('Segoe UI', 13), fg_color='#27ae60', hover_color='#1b7e46',
            width=130, height=38)
        self._btn_confirm.pack(side='left', padx=(0, 10))

        ctk.CTkButton(btn_frame, text='닫기', command=self.destroy,
                      font=('Segoe UI', 13), fg_color='#555555', hover_color='#666666',
                      width=90, height=38).pack(side='right')

        self._status_lbl = ctk.CTkLabel(btn_frame, text='매핑 분석 중...',
                                         font=('Segoe UI', 11), text_color='#888888')
        self._status_lbl.pack(side='left', padx=14)

        # === Treeview ===
        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill='both', expand=True, padx=20, pady=(0, 6))

        cols = ('row', 'module', 'item', 'db_key', 'qc_value',
                'confidence', 'source', 'action')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=18)

        for col, heading, width, anchor in [
            ('row',        'Row',        55,  'center'),
            ('module',     'Module',    130,  'w'),
            ('item',       'Check Item',280,  'w'),
            ('db_key',     'DB Key',    220,  'w'),
            ('qc_value',   'QC Value',   90,  'center'),
            ('confidence', 'Conf.',      60,  'center'),
            ('source',     'Source',     80,  'center'),
            ('action',     'Action',     70,  'center'),
        ]:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=anchor)

        # Tag colours
        self.tree.tag_configure('explicit', background='#E8F5E9')
        self.tree.tag_configure('learned',  background='#E8F5E9')
        self.tree.tag_configure('exact',    background='#E8F5E9')
        self.tree.tag_configure('fuzzy',    background='#FFF8E1')
        self.tree.tag_configure('unit_hint',background='#FFF8E1')
        self.tree.tag_configure('unmapped', background='#FFEBEE')

        sb_y = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        sb_x = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        sb_y.pack(side='right', fill='y')
        sb_x.pack(side='bottom', fill='x')
        self.tree.pack(fill='both', expand=True)

    # -----------------------------------------------------------------------
    # Mapping (background thread)
    # -----------------------------------------------------------------------

    def _run_mapping_async(self):
        threading.Thread(target=self._do_mapping, daemon=True).start()

    def _do_mapping(self):
        try:
            from src.core.checklist_autofiller import ChecklistAutoFiller
            filler = ChecklistAutoFiller(
                excel_path=self.excel_path,
                qc_report=self.qc_report,
                sync_manager=self.sync_manager,
                model=self.model,
                dry_run=True,
                confidence_threshold=self._get_threshold(),
                write_db_key_column=False,
            )
            import openpyxl, fnmatch
            wb = openpyxl.load_workbook(str(self.excel_path), data_only=False)
            ws = filler._find_main_sheet(wb)
            rows = filler._collect_rows(ws) if ws else []

            learned = []
            if self.sync_manager:
                learned = self.sync_manager._load_local_mappings(self.model)

            from src.core.checklist_mapper import ChecklistMapper
            mapper = ChecklistMapper(
                qc_lookup=filler._qc_lookup,
                learned_mappings=learned,
                model=self.model,
                fuzzy_threshold=self._get_threshold(),
            )
            self._map_results = mapper.map_rows(rows)
            self.after(0, self._populate_tree)
        except Exception as e:
            logger.error(f'Mapping failed: {e}', exc_info=True)
            self.after(0, lambda: self._status_lbl.configure(text=f'오류: {e}'))

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())

        counts = {'filled': 0, 'learned': 0, 'fuzzy': 0,
                  'unmapped': 0, 'protected': 0}

        for r in self._map_results:
            source = r.source
            qc_val = self._get_qc_value(r.db_key) if r.db_key else ''
            conf_str = f'{r.confidence:.2f}' if r.confidence > 0 else '-'
            action = 'Fill' if r.db_key else 'Skip'

            tag = source if source in ('explicit', 'learned', 'exact',
                                       'fuzzy', 'unit_hint', 'unmapped') else 'unmapped'

            self.tree.insert('', 'end', iid=str(r.row), tags=(tag,), values=(
                r.row, r.module, r.item,
                r.db_key or '(unmapped)',
                qc_val, conf_str, source, action,
            ))

            if source == 'unmapped':
                counts['unmapped'] += 1
            elif source == 'fuzzy':
                counts['fuzzy'] += 1
                counts['filled'] += 1
            elif source == 'learned':
                counts['learned'] += 1
                counts['filled'] += 1
            else:
                counts['filled'] += 1

        for key, lbl in self._stat_labels.items():
            lbl.configure(text=str(counts.get(key, '-')))

        self._status_lbl.configure(text=f'{len(self._map_results)}행 분석 완료')

    def _get_qc_value(self, db_key: str) -> str:
        from src.core.checklist_validator import ChecklistValidator
        val = ChecklistValidator()._build_qc_lookup(self.qc_report).get(db_key, '')
        return str(val) if val is not None else ''

    def _get_threshold(self) -> float:
        try:
            return float(self._threshold_var.get())
        except ValueError:
            return 0.80

    # -----------------------------------------------------------------------
    # Button handlers
    # -----------------------------------------------------------------------

    def _on_dryrun(self):
        self._run_fill(dry_run=True)

    def _on_confirm(self):
        if not messagebox.askyesno(
            '확정 기입',
            f'"{Path(self.excel_path).name}"의 G열에 QC 값을 기입합니다.\n'
            '백업 파일이 자동 생성됩니다. 계속하시겠습니까?',
            parent=self
        ):
            return
        self._run_fill(dry_run=False)

    def _run_fill(self, dry_run: bool):
        self._btn_dryrun.configure(state='disabled')
        self._btn_confirm.configure(state='disabled')
        self._status_lbl.configure(text='처리 중...')

        def _worker():
            try:
                from src.core.checklist_autofiller import ChecklistAutoFiller
                filler = ChecklistAutoFiller(
                    excel_path=self.excel_path,
                    qc_report=self.qc_report,
                    sync_manager=self.sync_manager,
                    model=self.model,
                    dry_run=dry_run,
                    fill_metadata=self._fill_meta_var.get(),
                    confidence_threshold=self._get_threshold(),
                    write_db_key_column=self._write_dbkey_var.get(),
                )
                report = filler.run()
                self._report = report
                self.after(0, lambda: self._on_fill_done(report, dry_run))
            except Exception as e:
                logger.error(f'Fill failed: {e}', exc_info=True)
                self.after(0, lambda: messagebox.showerror('오류', str(e), parent=self))
            finally:
                self.after(0, self._enable_buttons)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_fill_done(self, report, dry_run: bool):
        mode = 'Dry-run' if dry_run else '확정 기입'
        detail = (
            f'{mode} 완료\n\n'
            f'기입: {report.filled}행\n'
            f'미매핑 건너뜀: {report.skipped_unmapped}행\n'
            f'수식 보호됨: {report.skipped_protected}행\n'
            f'충돌(기존값 다름): {report.conflicts}건\n'
        )
        if not dry_run:
            detail += f'\n백업 파일이 원본과 같은 폴더에 저장되었습니다.'

        messagebox.showinfo(f'{mode} 결과', detail, parent=self)
        self._status_lbl.configure(text=f'{mode}: {report.filled}행 처리')

        # Re-run mapping display with results highlighted
        self._run_mapping_async()

    def _enable_buttons(self):
        self._btn_dryrun.configure(state='normal')
        self._btn_confirm.configure(state='normal')
