import * as sha256 from "fast-sha256";

class Utils {
    localstorage_keys = {
        HTTP_ACCESS_LOG_PER_PAGE: 'HTTP_ACCESS_LOG_PER_PAGE',
        DNS_LOG_PER_PAGE: 'DNS_LOG_PER_PAGE',
        SYSTEM_LOG_PER_PAGE: 'SYSTEM_LOG_PER_PAGE',
        CURRENT_USERNAME: 'CURRENT_USERNAME',
        CURRENT_USERTYPE: 'CURRENT_USERTYPE',
        AUTHORIZATION: "Authorization",
        HTTP_ACCESS_LOG_NOTIFICATION: "HTTP_ACCESS_LOG_NOTIFICATION",
        DNS_LOG_NOTIFICATION: "DNS_LOG_NOTIFICATION"
    };

    user_type = {
        USER_TYPE_ADMIN: 1,
        USER_TYPE_NORMAL: 2,
    };

    rule_type = {
        RULE_TYPE_STATIC_FILE: 1,
        RULE_TYPE_DYNAMIC_TEMPLATE: 2
    };

    body_type = {
        BODY_TYPE_NORMAL: 1,
        BODY_TYPE_ESCAPED: 2,
        BODY_TYPE_TOO_LONG: 3,
    };

    websocket_message_type = {
        NEW_HTTP_ACCESS_LOG: 1,
        NEW_DNS_LOG: 2
    };

    dns_class_map = {
        1: "IN",
        3: "CH",
        4: "HS"
    };

    dns_type_map = {
        1: 'A', 2: 'NS', 5: 'CNAME', 6: 'SOA', 10: 'NULL', 12: 'PTR', 13: 'HINFO',
        15: 'MX', 16: 'TXT', 17: 'RP', 18: 'AFSDB', 24: 'SIG', 25: 'KEY',
        28: 'AAAA', 29: 'LOC', 33: 'SRV', 35: 'NAPTR', 36: 'KX',
        37: 'CERT', 38: 'A6', 39: 'DNAME', 41: 'OPT', 42: 'APL',
        43: 'DS', 44: 'SSHFP', 45: 'IPSECKEY', 46: 'RRSIG', 47: 'NSEC',
        48: 'DNSKEY', 49: 'DHCID', 50: 'NSEC3', 51: 'NSEC3PARAM',
        52: 'TLSA', 53: 'HIP', 55: 'HIP', 59: 'CDS', 60: 'CDNSKEY',
        61: 'OPENPGPKEY', 62: 'CSYNC', 63: 'ZONEMD', 64: 'SVCB',
        65: 'HTTPS', 99: 'SPF', 108: 'EUI48', 109: 'EUI64', 249: 'TKEY',
        250: 'TSIG', 251: 'IXFR', 252: 'AXFR', 255: 'ANY', 256: 'URI',
        257: 'CAA', 32768: 'TA', 32769: 'DLV'
    };

    dns_type_reverse_map = {
        'A': 1,
        'NS': 2,
        'CNAME': 5,
        'SOA': 6,
        'NULL': 10,
        'PTR': 12,
        'HINFO': 13,
        'MX': 15,
        'TXT': 16,
        'RP': 17,
        'AFSDB': 18,
        'SIG': 24,
        'KEY': 25,
        'AAAA': 28,
        'LOC': 29,
        'SRV': 33,
        'NAPTR': 35,
        'KX': 36,
        'CERT': 37,
        'A6': 38,
        'DNAME': 39,
        'OPT': 41,
        'APL': 42,
        'DS': 43,
        'SSHFP': 44,
        'IPSECKEY': 45,
        'RRSIG': 46,
        'NSEC': 47,
        'DNSKEY': 48,
        'DHCID': 49,
        'NSEC3': 50,
        'NSEC3PARAM': 51,
        'TLSA': 52,
        'HIP': 55,
        'CDS': 59,
        'CDNSKEY': 60,
        'OPENPGPKEY': 61,
        'CSYNC': 62,
        'ZONEMD': 63,
        'SVCB': 64,
        'HTTPS': 65,
        'SPF': 99,
        'EUI48': 108,
        'EUI64': 109,
        'TKEY': 249,
        'TSIG': 250,
        'IXFR': 251,
        'AXFR': 252,
        'ANY': 255,
        'URI': 256,
        'CAA': 257,
        'TA': 32768,
        'DLV': 32769
    };


    save_localstorage(key, value) {
        window.localStorage.setItem(key, JSON.stringify(value));
    }

    load_localstorage(key, default_value = null) {
        let result = JSON.parse(window.localStorage.getItem(key));
        if (result === null) {
            return default_value;
        } else {
            return result;
        }
    }

    to_local_time(s) {
        let ts = Date.parse(s);
        let dummy = new Date();
        ts -= dummy.getTimezoneOffset() * 60 * 1000;
        let local_date = new Date(ts);
        return local_date.getFullYear() + '-' + (local_date.getMonth() + 1) + '-' + local_date.getDate() + ' '
            + local_date.getHours().toString().padStart(2, '0') + ':' + local_date.getMinutes().toString().padStart(2, '0')
            + ':' + local_date.getSeconds().toString().padStart(2, '0');
    }

    to_utc_time(s) {
        let ts = Date.parse(s);
        let dummy = new Date();
        ts += dummy.getTimezoneOffset() * 60 * 1000;
        let utc_date = new Date(ts);
        return utc_date.getFullYear() + '-' + (utc_date.getMonth() + 1) + '-' + utc_date.getDate() + ' '
            + utc_date.getHours().toString().padStart(2, '0') + ':' + utc_date.getMinutes().toString().padStart(2, '0')
            + ':' + utc_date.getSeconds().toString().padStart(2, '0');
    }

    buf_to_hex(buffer) { // buffer is an ArrayBuffer
        return [...new Uint8Array(buffer)]
            .map(x => x.toString(16).padStart(2, '0'))
            .join('');
    }

    pbkdf2(password, username) {
        let encoder = new TextEncoder();
        password = sha256.pbkdf2(encoder.encode(password), encoder.encode(username), 23333, 32);
        return utils.buf_to_hex(password);
    }

    parse_url(url) { // stupid URL api :(
        let l = document.createElement("a");
        l.href = url;
        return l;
    }
}

let utils = new Utils();
export default utils;
