from __future__ import annotations

from .. import machine as M
from .. import gmprep as Gmpmod


class _ComparisonNatMixin:
    def _seconds_text(self, total_seconds):
        if total_seconds < 60.0:
            return "{:.0f}s".format(total_seconds)
        if total_seconds < 3600.0:
            minutes = total_seconds / 60.0
            return "{:.1f}m".format(minutes)
        hours = total_seconds / 3600.0
        return "{:.1f}h".format(hours)

    def _nat_text(self, value):
        if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
            return "0"
        try:
            return Gmpmod.GMPRepText(value())()
        except Exception:
            pass
        rep = M.NatRepOf(value, self.registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            return Gmpmod.GMPRepText(rep)()
        return M.PrettyTerm(value, self.registry)()

    def _succ_nat_local(self, value):
        if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
            value = M.Zero
        try:
            succ_text = Gmpmod.GMPSuccText(Gmpmod.GMPRepText(value())())()
            if Gmpmod.GMPEqualText(succ_text, "0")() is M.truth_value:
                return M.Zero
            if Gmpmod.GMPEqualText(succ_text, "1")() is M.truth_value:
                return M.one
            if Gmpmod.GMPEqualText(succ_text, "2")() is M.truth_value:
                return M.two
            if Gmpmod.GMPEqualText(succ_text, "3")() is M.truth_value:
                return M.three
            if Gmpmod.GMPEqualText(succ_text, "4")() is M.truth_value:
                return M.four
            if Gmpmod.GMPEqualText(succ_text, "5")() is M.truth_value:
                return M.five
            if Gmpmod.GMPEqualText(succ_text, "6")() is M.truth_value:
                return M.six
            if Gmpmod.GMPEqualText(succ_text, "7")() is M.truth_value:
                return M.seven
            if Gmpmod.GMPEqualText(succ_text, "8")() is M.truth_value:
                return M.eight
            if Gmpmod.GMPEqualText(succ_text, "9")() is M.truth_value:
                return M.nine
            succ = M.Atom()
            succ.value = Gmpmod.GMPRep(succ_text)
            return succ
        except Exception:
            pass
        rep = M.NatRepOf(value, self.registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            succ_text = Gmpmod.GMPSuccText(Gmpmod.GMPRepText(rep)())()
            if Gmpmod.GMPEqualText(succ_text, "0")() is M.truth_value:
                return M.Zero
            if Gmpmod.GMPEqualText(succ_text, "1")() is M.truth_value:
                return M.one
            if Gmpmod.GMPEqualText(succ_text, "2")() is M.truth_value:
                return M.two
            if Gmpmod.GMPEqualText(succ_text, "3")() is M.truth_value:
                return M.three
            if Gmpmod.GMPEqualText(succ_text, "4")() is M.truth_value:
                return M.four
            if Gmpmod.GMPEqualText(succ_text, "5")() is M.truth_value:
                return M.five
            if Gmpmod.GMPEqualText(succ_text, "6")() is M.truth_value:
                return M.six
            if Gmpmod.GMPEqualText(succ_text, "7")() is M.truth_value:
                return M.seven
            if Gmpmod.GMPEqualText(succ_text, "8")() is M.truth_value:
                return M.eight
            if Gmpmod.GMPEqualText(succ_text, "9")() is M.truth_value:
                return M.nine
            succ = M.Atom()
            succ.value = Gmpmod.GMPRep(succ_text)
            return succ
        pair = M.Succ(value, self.registry)()
        self.registry = M.Head(M.Tail(pair)())()
        return M.Head(pair)()

    def _nat_add_local(self, left, right):
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            left = M.Zero
        if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            right = M.Zero
        try:
            sum_text = Gmpmod.GMPAddText(
                Gmpmod.GMPRepText(left())(),
                Gmpmod.GMPRepText(right())(),
            )()
            if Gmpmod.GMPEqualText(sum_text, "0")() is M.truth_value:
                return M.Zero
            if Gmpmod.GMPEqualText(sum_text, "1")() is M.truth_value:
                return M.one
            if Gmpmod.GMPEqualText(sum_text, "2")() is M.truth_value:
                return M.two
            if Gmpmod.GMPEqualText(sum_text, "3")() is M.truth_value:
                return M.three
            if Gmpmod.GMPEqualText(sum_text, "4")() is M.truth_value:
                return M.four
            if Gmpmod.GMPEqualText(sum_text, "5")() is M.truth_value:
                return M.five
            if Gmpmod.GMPEqualText(sum_text, "6")() is M.truth_value:
                return M.six
            if Gmpmod.GMPEqualText(sum_text, "7")() is M.truth_value:
                return M.seven
            if Gmpmod.GMPEqualText(sum_text, "8")() is M.truth_value:
                return M.eight
            if Gmpmod.GMPEqualText(sum_text, "9")() is M.truth_value:
                return M.nine
            total = M.Atom()
            total.value = Gmpmod.GMPRep(sum_text)
            return total
        except Exception:
            pass
        left_rep = M.NatRepOf(left, self.registry)()
        right_rep = M.NatRepOf(right, self.registry)()
        if M.IdentityCompare(left_rep, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(right_rep, M.EmptyList)() is M.false_value:
                sum_text = Gmpmod.GMPAddText(
                    Gmpmod.GMPRepText(left_rep)(),
                    Gmpmod.GMPRepText(right_rep)(),
                )()
                if Gmpmod.GMPEqualText(sum_text, "0")() is M.truth_value:
                    return M.Zero
                if Gmpmod.GMPEqualText(sum_text, "1")() is M.truth_value:
                    return M.one
                if Gmpmod.GMPEqualText(sum_text, "2")() is M.truth_value:
                    return M.two
                if Gmpmod.GMPEqualText(sum_text, "3")() is M.truth_value:
                    return M.three
                if Gmpmod.GMPEqualText(sum_text, "4")() is M.truth_value:
                    return M.four
                if Gmpmod.GMPEqualText(sum_text, "5")() is M.truth_value:
                    return M.five
                if Gmpmod.GMPEqualText(sum_text, "6")() is M.truth_value:
                    return M.six
                if Gmpmod.GMPEqualText(sum_text, "7")() is M.truth_value:
                    return M.seven
                if Gmpmod.GMPEqualText(sum_text, "8")() is M.truth_value:
                    return M.eight
                if Gmpmod.GMPEqualText(sum_text, "9")() is M.truth_value:
                    return M.nine
                total = M.Atom()
                total.value = Gmpmod.GMPRep(sum_text)
                return total
        pair = M.Add(left, right, self.registry)()
        self.registry = M.Head(M.Tail(pair)())()
        return M.Head(pair)()

    def _nat_max_local(self, left, right):
        if M.NatLess(left, right, self.registry)() is M.truth_value:
            return right
        return left

    def _nat_min_local(self, left, right):
        if M.NatLess(left, right, self.registry)() is M.truth_value:
            return left
        return right

    def _pred_nat_or_zero_local(self, value):
        if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
            return M.Zero
        try:
            pred_text = Gmpmod.GMPPredText(Gmpmod.GMPRepText(value())())()
            if Gmpmod.GMPEqualText(pred_text, "0")() is M.truth_value:
                return M.Zero
            pred = M.Atom()
            pred.value = Gmpmod.GMPRep(pred_text)
            return pred
        except Exception:
            pass
        rep = M.NatRepOf(value, self.registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            pred_text = Gmpmod.GMPPredText(Gmpmod.GMPRepText(rep)())()
            if Gmpmod.GMPEqualText(pred_text, "0")() is M.truth_value:
                return M.Zero
            pred = M.Atom()
            pred.value = Gmpmod.GMPRep(pred_text)
            return pred
        if M.NatEq(value, M.Zero, self.registry)() is M.truth_value:
            return M.Zero
        pred_pair = M.NatPred(value, self.registry)()
        pred = M.Head(pred_pair)()
        self.registry = M.Head(M.Tail(pred_pair)())()
        return pred

    def _nat_sub_or_zero_local(self, left, right):
        if M.NatEq(right, M.Zero, self.registry)() is M.truth_value:
            return left
        if M.NatEq(left, M.Zero, self.registry)() is M.truth_value:
            return M.Zero
        return self._nat_sub_or_zero_local(
            self._pred_nat_or_zero_local(left),
            self._pred_nat_or_zero_local(right),
        )



def sync_from_namespace(namespace):
    return None


__all__ = [name for name in globals() if not name.startswith("_") or name.startswith("_ComparisonNatMixin")]
