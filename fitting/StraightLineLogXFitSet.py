from typing import List
from fitting import Fit, FitSet, StraightLineLogXFit
from astropy.io import ascii


class StraightLineLogXFitSet(FitSet):
    """
    A set of StraightLineLogXFit types used to fit a range of data
    It handles the fact that the x-axis is represented in log10(x) form
    """

    @classmethod
    def _create_fitted_fit_on_data(
            cls, id: int, xi: List[float], yi: List[float], dyi: List[float], from_xi: float, to_xi: float) -> Fit:
        """
        Custom factory method for creating the fits associated with this set.
        """
        return StraightLineLogXFit.fit_to_data(id, xi, yi, dxi=None, dyi=dyi, range_from=from_xi, range_to=to_xi)

    def to_latex(self, caption: str = None) -> str:
        range_field = r"$\Delta t$ range [d]"
        table = {"Symbol": list(), range_field: list(), "Value": list()}
        for fit in self:
            table["Symbol"].append(f"$\\alpha_{{{fit.id}}}$")
            table[range_field].append(f"$({fit.range_from:.2f}, {fit.range_to:.2f})$")
            if isinstance(fit, StraightLineLogXFit):
                table["Value"].append(f"${fit.alpha:.3f}$".replace("+/-", r" \pm "))
            else:
                table["Value"].append("")

        ld = {
            "tabletype": "table",
            "tablealign": "ht",
            "preamble": r"\begin{center}",
            "col_align": "c c r",
            "header_start": r"\hline",
            "header_end": r"\hline",
            "data_start": r"\hline",
            "data_end": r"\hline",
            "tablefoot": r"\end{center}"}
        if caption is not None:
            ld["caption"] = caption

        return ascii.write(table, Writer=ascii.Latex, latexdict=ld)
