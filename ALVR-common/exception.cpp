#include <stdarg.h>
#include "exception.h"
#include "common-utils.h"

Exception FormatExceptionV(const wchar_t *format, va_list args) {
	wchar_t buf[10000];
	_vsnwprintf_s(buf, sizeof(buf) / sizeof(buf[0]), format, args);

	return Exception(buf);
}

Exception FormatExceptionV(const char *format, va_list args) {
	char buf[10000];
	_vsnprintf_s(buf, sizeof(buf) / sizeof(buf[0]), format, args);

	return Exception(ToWstring(buf));
}

Exception FormatException(const char *format, ...) {
	va_list args;
	va_start(args, format);
	Exception e = FormatExceptionV(format, args);
	va_end(args);

	return e;
}