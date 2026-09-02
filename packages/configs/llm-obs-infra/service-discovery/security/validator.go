package security

import (
	"errors"
	"fmt"
	"net"
	"regexp"
	"strings"
)

var (
	validHostnameRegex = regexp.MustCompile(`^[a-zA-Z0-9][-a-zA-Z0-9_.]*[a-zA-Z0-9]$`)
	privateIPBlocks    []*net.IPNet
)

func init() {
	for _, cidr := range []string{
		"10.0.0.0/8",     // RFC 1918 Class A
		"172.16.0.0/12",  // RFC 1918 Class B (including docker default 172.17 - 172.28)
		"192.168.0.0/16", // RFC 1918 Class C
		"fc00::/7",       // Unique Local IPv6
	} {
		_, block, _ := net.ParseCIDR(cidr)
		privateIPBlocks = append(privateIPBlocks, block)
	}
}

func ValidateEndpoint(host string, port int, enforceRFC1918 bool) error {
	if host == "" {
		return errors.New("host cannot be empty")
	}

	if port < 1 || port > 65535 {
		return fmt.Errorf("port %d is outside valid range (1-65535)", port)
	}

	ip := net.ParseIP(host)
	if ip != nil {
		if ip.IsLinkLocalUnicast() || ip.String() == "169.254.169.254" {
			return errors.New("cloud metadata (169.254.169.254) and link-local addresses are prohibited")
		}
		if enforceRFC1918 {
			if ip.IsLoopback() {
				return errors.New("loopback addresses (127.0.0.0/8, ::1) are prohibited in production")
			}
			isPrivate := false
			for _, block := range privateIPBlocks {
				if block.Contains(ip) {
					isPrivate = true
					break
				}
			}
			if !isPrivate {
				return fmt.Errorf("IP address %s is not within allowed RFC 1918 private subnets", host)
			}
		}
		return nil
	}

	// Hostname validation
	if enforceRFC1918 && strings.EqualFold(host, "localhost") {
		return errors.New("localhost is prohibited in production")
	}

	if !validHostnameRegex.MatchString(host) {
		return fmt.Errorf("invalid hostname format: %s", host)
	}

	return nil
}

func ValidateProtocol(protocol string) error {
	switch strings.ToLower(protocol) {
	case "http", "tcp":
		return nil
	default:
		return fmt.Errorf("unsupported protocol %q: only 'http' and 'tcp' are permitted", protocol)
	}
}
