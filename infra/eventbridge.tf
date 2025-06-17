locals {
  regions = {
    auckland = {
      name                 = "Auckland"
      slug                 = "auckland"
      country              = "NZ"
      scrape_cinemas_cron  = "cron(0 0 1 1,7 ? *)"
      scrape_sessions_cron = "cron(0 0 ? * 1 *)"
    }
    canterbury = {
      name                 = "Canterbury"
      slug                 = "canterbury"
      country              = "NZ"
      scrape_cinemas_cron  = "cron(5 0 1 1,7 ? *)"
      scrape_sessions_cron = "cron(2 0 ? * 1 *)"
    }
    brisbane_central = {
      name                 = "Brisbane Central"
      slug                 = "brisbane-central"
      country              = "AU"
      scrape_cinemas_cron  = "cron(10 0 1 1,7 ? *)"
      scrape_sessions_cron = "cron(4 0 ? * 1 *)"
    }
  }
}

resource "aws_cloudwatch_event_rule" "scrape_cinemas_cron" {
  for_each = local.regions

  name                = "${local.application}_scrape_cinemas_cron_${each.key}"
  schedule_expression = each.value.scrape_cinemas_cron
}

resource "aws_cloudwatch_event_target" "scrape_cinemas_cron_job" {
  for_each = local.regions

  rule      = aws_cloudwatch_event_rule.scrape_cinemas_cron[each.key].name
  target_id = "${local.application}_scrape_cinemas_cron_job_${each.key}"
  arn       = aws_lambda_function.scrape_cinemas.arn

  input = jsonencode({
    region_name  = each.value.name
    region_slug  = each.value.slug
    country_code = each.value.country
  })
}

resource "aws_lambda_permission" "scrape_cinemas_allow_eventbridge" {
  for_each = local.regions

  statement_id  = "${local.application}_AllowExecutionFromEventBridge_${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scrape_cinemas.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scrape_cinemas_cron[each.key].arn
}

resource "aws_cloudwatch_event_rule" "scrape_sessions_cron" {
  for_each = local.regions

  name                = "${local.application}_scrape_sessions_cron_${each.key}"
  schedule_expression = each.value.scrape_sessions_cron
}

resource "aws_cloudwatch_event_target" "scrape_sessions_cron_job" {
  for_each = local.regions

  rule      = aws_cloudwatch_event_rule.scrape_sessions_cron[each.key].name
  target_id = "${local.application}_scrape_sessions_cron_job_${each.key}"
  arn       = aws_lambda_function.scrape_sessions.arn

  input = jsonencode({
    region_name  = each.value.name
    region_slug  = each.value.slug
    country_code = each.value.country
  })
}

resource "aws_lambda_permission" "scrape_sessions_allow_eventbridge" {
  for_each = local.regions

  statement_id  = "${local.application}_AllowExecutionFromEventBridge_${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scrape_sessions.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scrape_sessions_cron[each.key].arn
}
