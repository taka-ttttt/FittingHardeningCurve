"""エクスポートサービス"""

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from app.core.models.fit_result import FitResult
from app.core.utils.fileio import ensure_directory


class ExportService:
    """エクスポートサービス"""
    
    def __init__(self, export_dir: Path | str = "data/fits"):
        """初期化
        
        Args:
            export_dir: エクスポート先ディレクトリ
        """
        self.export_dir = Path(export_dir)
        ensure_directory(self.export_dir)
    
    def export_result_json(
        self,
        result: FitResult,
        filepath: Path | str | None = None
    ) -> Path:
        """フィット結果をJSONでエクスポート
        
        Args:
            result: フィット結果
            filepath: 出力パス（Noneの場合は自動生成）
            
        Returns:
            Path: 保存先パス
        """
        if filepath is None:
            filepath = self.export_dir / f"{result.id}_result.json"
        else:
            filepath = Path(filepath)
        
        ensure_directory(filepath.parent)
        
        # Pydanticのmodel_dump_jsonを使用
        json_str = result.model_dump_json(indent=2)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        return filepath
    
    def export_result_csv(
        self,
        result: FitResult,
        filepath: Path | str | None = None
    ) -> Path:
        """フィット結果をCSVでエクスポート
        
        Args:
            result: フィット結果
            filepath: 出力パス（Noneの場合は自動生成）
            
        Returns:
            Path: 保存先パス
        """
        if filepath is None:
            filepath = self.export_dir / f"{result.id}_data.csv"
        else:
            filepath = Path(filepath)
        
        ensure_directory(filepath.parent)
        
        # データフレームを作成
        df = pd.DataFrame({
            'x': result.x_data,
            'y_actual': result.y_data,
            'y_fitted': result.y_fitted,
            'residual': result.residuals
        })
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return filepath
    
    def export_parameters_csv(
        self,
        result: FitResult,
        filepath: Path | str | None = None
    ) -> Path:
        """パラメータをCSVでエクスポート
        
        Args:
            result: フィット結果
            filepath: 出力パス
            
        Returns:
            Path: 保存先パス
        """
        if filepath is None:
            filepath = self.export_dir / f"{result.id}_parameters.csv"
        else:
            filepath = Path(filepath)
        
        ensure_directory(filepath.parent)
        
        # パラメータと誤差を結合
        data = {
            'parameter': list(result.parameters.keys()),
            'value': list(result.parameters.values())
        }
        
        if result.parameter_errors:
            data['error'] = [
                result.parameter_errors.get(p, None)
                for p in result.parameters.keys()
            ]
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return filepath
    
    def export_statistics_json(
        self,
        result: FitResult,
        filepath: Path | str | None = None
    ) -> Path:
        """統計情報をJSONでエクスポート
        
        Args:
            result: フィット結果
            filepath: 出力パス
            
        Returns:
            Path: 保存先パス
        """
        if filepath is None:
            filepath = self.export_dir / f"{result.id}_statistics.json"
        else:
            filepath = Path(filepath)
        
        ensure_directory(filepath.parent)
        
        stats_dict = result.statistics.model_dump()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(stats_dict, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def export_plot_image(
        self,
        figure: go.Figure,
        filepath: Path | str,
        format: str = 'png',
        width: int = 1200,
        height: int = 800
    ) -> Path:
        """グラフを画像でエクスポート
        
        Args:
            figure: Plotlyフィギュア
            filepath: 出力パス
            format: 画像フォーマット（png, svg, jpg, webp）
            width: 画像幅
            height: 画像高さ
            
        Returns:
            Path: 保存先パス
        """
        filepath = Path(filepath)
        ensure_directory(filepath.parent)
        
        # 拡張子がない場合は追加
        if not filepath.suffix:
            filepath = filepath.with_suffix(f'.{format}')
        
        # 画像として保存
        figure.write_image(
            str(filepath),
            format=format,
            width=width,
            height=height
        )
        
        return filepath
    
    def export_plot_html(
        self,
        figure: go.Figure,
        filepath: Path | str | None = None
    ) -> Path:
        """グラフをHTMLでエクスポート
        
        Args:
            figure: Plotlyフィギュア
            filepath: 出力パス
            
        Returns:
            Path: 保存先パス
        """
        if filepath is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.export_dir / f"plot_{timestamp}.html"
        else:
            filepath = Path(filepath)
        
        ensure_directory(filepath.parent)
        
        figure.write_html(str(filepath))
        
        return filepath
    
    def create_summary_report(
        self,
        result: FitResult,
        filepath: Path | str | None = None
    ) -> Path:
        """サマリーレポートを作成
        
        Args:
            result: フィット結果
            filepath: 出力パス
            
        Returns:
            Path: 保存先パス
        """
        if filepath is None:
            filepath = self.export_dir / f"{result.id}_report.txt"
        else:
            filepath = Path(filepath)
        
        ensure_directory(filepath.parent)
        
        # レポート生成
        lines = [
            "=" * 60,
            "フィッティング結果レポート",
            "=" * 60,
            f"結果ID: {result.id}",
            f"名前: {result.name or 'N/A'}",
            f"作成日時: {result.created_at}",
            f"データセットID: {result.dataset_id}",
            "",
            "モデル情報",
            "-" * 60,
            f"手法: {result.config.method}",
            f"関数: {result.get_fit_function_str()}",
            "",
            "パラメータ",
            "-" * 60,
        ]
        
        for param, value in result.parameters.items():
            error_str = ""
            if result.parameter_errors and param in result.parameter_errors:
                error = result.parameter_errors[param]
                error_str = f" ± {error:.6g}"
            lines.append(f"{param}: {value:.6g}{error_str}")
        
        lines.extend([
            "",
            "統計指標",
            "-" * 60,
            f"R²: {result.statistics.r_squared:.6f}",
            f"調整済みR²: {result.statistics.adjusted_r_squared:.6f}",
            f"RMSE: {result.statistics.rmse:.6g}",
            f"MAE: {result.statistics.mae:.6g}",
            f"最大誤差: {result.statistics.max_error:.6g}",
            f"AIC: {result.statistics.aic:.6g}",
            f"BIC: {result.statistics.bic:.6g}",
            "",
            "データ情報",
            "-" * 60,
            f"データ点数: {len(result.x_data)}",
            f"X範囲: [{result.x_data.min():.6g}, {result.x_data.max():.6g}]",
            f"Y範囲: [{result.y_data.min():.6g}, {result.y_data.max():.6g}]",
            "",
            "=" * 60,
        ])
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return filepath

