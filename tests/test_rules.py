import unittest

from ci_checker.model import Container, Instance
from ci_checker.rules import (
    exit_code,
    rule_job_restart_always,
    rule_no_graceful_shutdown,
    rule_prod_unpinned_image,
    rule_secret_env,
    run_all,
)


def cont(name="c", image="reg/app:v1.0.0", env=()):
    return Container(name=name, image_url=image, env=tuple(env))


def inst(name="i", labels=("prod",), policy="ALWAYS", timeout=30, containers=(cont(),)):
    return Instance(name=name, labels=tuple(labels), restart_policy=policy,
                    shutdown_timeout=timeout, containers=tuple(containers))


class TestCins001(unittest.TestCase):
    def test_fires_secret_like(self):
        out = rule_secret_env((inst(containers=(cont(env=(("DB_PASSWORD", "x"),)),)),))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "HIGH")

    def test_fires_token_and_api_key(self):
        out = rule_secret_env((inst(containers=(cont(env=(("AUTH_TOKEN", "t"), ("STRIPE_API_KEY", "k"))),)),))
        self.assertEqual(len(out), 1)
        self.assertIn("AUTH_TOKEN", out[0].detail)

    def test_quiet_empty_value(self):
        self.assertEqual(rule_secret_env((inst(containers=(cont(env=(("DB_PASSWORD", ""),)),)),)), [])

    def test_quiet_normal_env(self):
        self.assertEqual(rule_secret_env((inst(containers=(cont(env=(("LOG_LEVEL", "info"),)),)),)), [])


class TestCins002(unittest.TestCase):
    def test_fires_batch_always(self):
        out = rule_job_restart_always((inst(labels=("batch",), policy="ALWAYS"),))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "MEDIUM")

    def test_quiet_batch_on_failure(self):
        self.assertEqual(rule_job_restart_always((inst(labels=("cron",), policy="ON_FAILURE"),)), [])

    def test_quiet_prod_always(self):
        self.assertEqual(rule_job_restart_always((inst(labels=("prod",), policy="ALWAYS"),)), [])


class TestCins003(unittest.TestCase):
    def test_fires_no_tag(self):
        out = rule_prod_unpinned_image((inst(containers=(cont(image="reg/app"),)),))
        self.assertEqual(len(out), 1)

    def test_fires_latest_tag(self):
        out = rule_prod_unpinned_image((inst(containers=(cont(image="reg/app:latest"),)),))
        self.assertEqual(len(out), 1)

    def test_quiet_pinned(self):
        self.assertEqual(rule_prod_unpinned_image((inst(containers=(cont(image="reg/app:v2.1.0"),)),)), [])

    def test_quiet_dev_label(self):
        self.assertEqual(rule_prod_unpinned_image((inst(labels=("dev",), containers=(cont(image="reg/app"),)),)), [])

    def test_port_in_registry_not_tag(self):
        out = rule_prod_unpinned_image((inst(containers=(cont(image="reg:5000/app"),)),))
        self.assertEqual(len(out), 1)


class TestCins004(unittest.TestCase):
    def test_fires_zero(self):
        out = rule_no_graceful_shutdown((inst(timeout=0),))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "LOW")

    def test_quiet_positive(self):
        self.assertEqual(rule_no_graceful_shutdown((inst(timeout=15),)), [])


class TestAggregation(unittest.TestCase):
    def test_exit_2_on_high(self):
        self.assertEqual(exit_code(run_all((inst(containers=(cont(env=(("APP_SECRET", "x"),)),)),))), 2)

    def test_exit_1_medium_only(self):
        self.assertEqual(exit_code(run_all((inst(labels=("batch",), timeout=30),))), 1)

    def test_exit_0_clean(self):
        self.assertEqual(exit_code(run_all((inst(),))), 0)


if __name__ == "__main__":
    unittest.main()
