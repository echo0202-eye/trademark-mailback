# 接口说明（内部）

技能通过朱门商标公开查询接口读取数据，均为 POST JSON，只读。

基础地址：

```
https://www.zhumen.com.cn/leads/miniapp/api/index.php?action=mailback&op=<op>
Content-Type: application/json
```

认证方式（二选一）：

1. 请求头 `X-Api-Key: <key>`（推荐，外部 Skill 使用）
2. 请求体 `"source": "mp_mailback"`（小程序通道）

API Key 通道仅开放 `search`、`company` 两个只读接口，其余 op 返回 `forbidden_op`。

## op=search

按公司名模糊搜索，最少 2 个字。

请求：

```json
{ "q": "乐乐农业", "source": "mp_mailback" }
```

返回：

```json
{
  "ok": true,
  "q": "乐乐农业",
  "total": 3,
  "items": [
    { "applicant": "乐乐农业（深圳）有限公司", "n": 2, "ggCnt": 2, "lastGg": "1720", "lastDate": "2020-11-20" }
  ]
}
```

字段：`n` 为退信件数，`ggCnt` 为涉及公告期数，`lastGg/lastDate` 为最近一期。

## op=company

按申请人全名查询明细，支持分页（每页 100）。

请求：

```json
{ "applicant": "乐乐农业（深圳）有限公司", "offset": 0, "source": "mp_mailback" }
```

返回：

```json
{
  "ok": true,
  "applicant": "乐乐农业（深圳）有限公司",
  "total": 2,
  "shown": 2,
  "offset": 0,
  "limit": 100,
  "hasMore": false,
  "rows": [
    {
      "gonggaoNo": "1720",
      "gonggaoDate": "2020-11-20",
      "gonggaoType": "送达公告",
      "regNo": "27287426",
      "markName": "KAPA",
      "typeText": "",
      "typeState": "none",
      "fileUrl": "https://zm-mailback-1308910937.cos.ap-beijing.myqcloud.com/mailback/...",
      "fileKind": "img",
      "deadline": {
        "deliverDate": "2020-12-20",
        "daysToDeliver": -2163,
        "hasType": false,
        "typeText": "",
        "deadlineDate": "",
        "daysLeft": 0,
        "state": "unknown",
        "hint": "已于 2020-12-20 视为送达，具体期限以通知书载明为准",
        "short": "12-20 视为送达",
        "urgent": false
      }
    }
  ]
}
```

说明：

- `typeText` 为空表示发文类型尚未识别。
- `fileUrl` 仅在公告原件已归档时返回（COS 地址）。
- `deadline` 由服务端按公告日期与发文类型推算，仅供参考。

## 错误码

| error | 含义 |
|---|---|
| `invalid_source` | 请求体缺少 `source` 或值不对 |
| `q_too_short` | 搜索词少于 2 个字 |
| `invalid_applicant` | 公司名为空或过长 |
| `not_found` | 公告库中没有该公司的退信记录 |
| `rate_limited` | 超过每小时 60 次限频 |

## 限频

搜索与明细共用 60 次/小时（按 IP）。批量查询时建议本地缓存结果。
